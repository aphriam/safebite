from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .models import (
    UserAllergyProfile, UserAllergy, PredictionHistory,
    MedicineCheckHistory, DrugInteractionHistory, SymptomLog
)
from .ml_model import predict_risk
from .medicine_module import (
    check_medicine_allergens,
    check_drug_interactions,
    analyze_symptoms,
    search_medicine
)


# ═══════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    UserAllergyProfile.objects.create(user=user)
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'message': 'Account created successfully',
        'token': token.key,
        'username': user.username
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=401)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'username': user.username})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})


# ═══════════════════════════════════════════
# ALLERGY PROFILE
# ═══════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    profile, _ = UserAllergyProfile.objects.get_or_create(user=request.user)
    allergies = profile.allergies.all().values(
        'id', 'allergen_name', 'item_type', 'symptoms', 'severity', 'notes', 'created_at'
    )
    return Response({
        'username': request.user.username,
        'email': request.user.email,
        'allergies': list(allergies),
        'total_allergies': profile.allergies.count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_allergy(request):
    allergen_name = request.data.get('allergen_name')
    if not allergen_name:
        return Response({'error': 'allergen_name is required'}, status=400)

    profile, _ = UserAllergyProfile.objects.get_or_create(user=request.user)
    allergy = UserAllergy.objects.create(
        profile=profile,
        allergen_name=allergen_name,
        item_type=request.data.get('item_type', 'food'),
        symptoms=request.data.get('symptoms', ''),
        severity=request.data.get('severity', 'mild'),
        notes=request.data.get('notes', '')
    )
    return Response({
        'message': 'Allergy added successfully',
        'allergy': {
            'id': allergy.id,
            'allergen_name': allergy.allergen_name,
            'item_type': allergy.item_type,
            'severity': allergy.severity,
            'symptoms': allergy.symptoms,
        }
    }, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_allergy(request, allergy_id):
    try:
        profile = UserAllergyProfile.objects.get(user=request.user)
        allergy = profile.allergies.get(id=allergy_id)
        allergy.delete()
        return Response({'message': 'Allergy removed successfully'})
    except UserAllergy.DoesNotExist:
        return Response({'error': 'Allergy not found'}, status=404)


# ═══════════════════════════════════════════
# FOOD PREDICTION
# ═══════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_food_allergy(request):
    item_name = request.data.get('item_name', '')
    ingredients = request.data.get('ingredients', '')
    item_type = request.data.get('item_type', 'food')

    if not ingredients and not item_name:
        return Response({'error': 'item_name or ingredients required'}, status=400)

    full_text = f"{item_name} {ingredients}".strip()

    try:
        profile = UserAllergyProfile.objects.get(user=request.user)
        # Only use FOOD allergies for food check
        user_allergies = list(profile.allergies.filter(item_type='food').values_list('allergen_name', flat=True))
    except UserAllergyProfile.DoesNotExist:
        user_allergies = []

    result = predict_risk(full_text, user_allergies, item_name=item_name)

    PredictionHistory.objects.create(
        user=request.user,
        item_name=item_name or full_text[:100],
        item_type=item_type,
        ingredients_text=ingredients or full_text,
        risk_level=result['risk'],
        confidence=result['confidence'],
        allergens_found=result['allergens_found'],
        matched_allergens=result['matched_allergens'],
        alternatives=result['alternatives'],
    )

    return Response({
        'item_name': item_name,
        'risk_level': result['risk'],
        'confidence_percent': f"{result['confidence']}%",
        'allergens_detected': result['allergens_found'],
        'matched_your_allergies': result['matched_allergens'],
        'safer_alternatives': result['alternatives'],
        'ml_model_prediction': result['ml_prediction'],
        'recommendation': (
            '🚨 HIGH RISK — Avoid this item!' if result['risk'] == 'high' else
            '⚠️ MEDIUM RISK — Consume with caution.' if result['risk'] == 'medium' else
            '✅ LOW RISK — Appears safe for you.'
        )
    })


# ═══════════════════════════════════════════
# MEDICINE CHECKER
# ═══════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_medicine(request):
    """
    Check if a medicine is safe based on user's allergy profile.

    Request:
    {
        "medicine_name": "Ibuprofen",
        "ingredients": "ibuprofen, cellulose"  // optional
    }
    """
    medicine_name = request.data.get('medicine_name')
    ingredients = request.data.get('ingredients', '')

    if not medicine_name:
        return Response({'error': 'medicine_name is required'}, status=400)

    try:
        profile = UserAllergyProfile.objects.get(user=request.user)
        # Only use MEDICINE allergies for medicine check
        user_allergies = list(profile.allergies.filter(item_type='medicine').values_list('allergen_name', flat=True))
    except UserAllergyProfile.DoesNotExist:
        user_allergies = []

    result = check_medicine_allergens(medicine_name, ingredients, user_allergies)

    # Save to history
    MedicineCheckHistory.objects.create(
        user=request.user,
        medicine_name=medicine_name,
        ingredients_text=ingredients,
        drug_class=result.get('drug_class', ''),
        risk_level=result['risk_level'],
        confidence=result['confidence'],
        allergens_found=result['allergens_found'],
        matched_allergens=result['matched_your_allergies'],
        alternative_medicines=result['alternative_medicines'],
        side_effects=result.get('side_effects', '')
    )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medicine_history(request):
    """Get user's medicine check history."""
    limit = int(request.query_params.get('limit', 20))
    checks = MedicineCheckHistory.objects.filter(user=request.user)[:limit].values(
        'id', 'medicine_name', 'drug_class', 'risk_level',
        'allergens_found', 'matched_allergens', 'alternative_medicines',
        'side_effects', 'created_at'
    )
    return Response({
        'total': MedicineCheckHistory.objects.filter(user=request.user).count(),
        'history': list(checks)
    })


# ═══════════════════════════════════════════
# DRUG INTERACTION CHECKER
# ═══════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def drug_interaction_check(request):
    """
    Check interactions between multiple medicines.

    Request:
    {
        "medicines": ["Ibuprofen", "Warfarin", "Aspirin"]
    }
    """
    medicines = request.data.get('medicines', [])

    if not medicines or len(medicines) < 2:
        return Response({'error': 'Please provide at least 2 medicines'}, status=400)

    result = check_drug_interactions(medicines)

    # Save to history
    DrugInteractionHistory.objects.create(
        user=request.user,
        medicines_checked=medicines,
        interactions_found=result['interactions'],
        total_interactions=result['total_interactions'],
        is_safe=result['safe']
    )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interaction_history(request):
    """Get user's drug interaction check history."""
    limit = int(request.query_params.get('limit', 20))
    history = DrugInteractionHistory.objects.filter(user=request.user)[:limit].values(
        'id', 'medicines_checked', 'total_interactions',
        'interactions_found', 'is_safe', 'created_at'
    )
    return Response({'history': list(history)})


# ═══════════════════════════════════════════
# MEDICINE SEARCH
# ═══════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_medicine_info(request):
    """
    Search medicine info from database.
    GET /api/medicine/search/?name=Ibuprofen
    """
    name = request.query_params.get('name')
    if not name:
        return Response({'error': 'name query parameter required'}, status=400)

    result = search_medicine(name)
    if result:
        return Response({'found': True, 'medicine': result})
    return Response({'found': False, 'message': f'Medicine "{name}" not found in database'})


# ═══════════════════════════════════════════
# SYMPTOM TRACKER
# ═══════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_symptoms(request):
    """
    Log and analyze symptoms.

    Request:
    {
        "symptoms": ["hives", "swelling", "itching"],
        "current_medicines": ["Ibuprofen", "Amoxicillin"],
        "recent_foods": "peanut butter sandwich, milk",
        "notes": "Started after lunch"
    }
    """
    symptoms = request.data.get('symptoms', [])
    current_medicines = request.data.get('current_medicines', [])
    recent_foods = request.data.get('recent_foods', '')
    notes = request.data.get('notes', '')

    if not symptoms:
        return Response({'error': 'symptoms list is required'}, status=400)

    try:
        profile = UserAllergyProfile.objects.get(user=request.user)
        user_allergies = list(profile.allergies.values_list("allergen_name", flat=True))
    except UserAllergyProfile.DoesNotExist:
        user_allergies = []

    result = analyze_symptoms(symptoms, current_medicines, recent_foods, user_allergies)

    # Save to history
    SymptomLog.objects.create(
        user=request.user,
        symptoms=symptoms,
        current_medicines=current_medicines,
        recent_foods=recent_foods,
        overall_severity=result['overall_severity'],
        possible_allergens=result['possible_allergens'],
        medicine_warnings=result['medicine_warnings'],
        notes=notes
    )

    return Response({
        'symptoms':               symptoms,
        'overall_severity':       result['overall_severity'],
        'possible_allergens':     result['possible_allergens'],
        'confirmed_from_profile': result['confirmed_from_profile'],
        'allergens_in_foods':     result['allergens_in_foods'],
        'medicine_warnings':      result['medicine_warnings'],
        'recommendation':         result['recommendation'],
        'next_steps':             result['next_steps'],
        'recent_foods_noted':     recent_foods,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def symptom_history(request):
    """Get user's symptom log history."""
    limit = int(request.query_params.get('limit', 20))
    logs = SymptomLog.objects.filter(user=request.user)[:limit].values(
        'id', 'symptoms', 'overall_severity', 'possible_allergens',
        'medicine_warnings', 'recent_foods', 'notes', 'created_at'
    )
    return Response({
        'total': SymptomLog.objects.filter(user=request.user).count(),
        'logs': list(logs)
    })


# ═══════════════════════════════════════════
# FOOD HISTORY
# ═══════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prediction_history(request):
    limit = int(request.query_params.get('limit', 20))
    risk_filter = request.query_params.get('risk', None)
    qs = PredictionHistory.objects.filter(user=request.user)
    if risk_filter:
        qs = qs.filter(risk_level=risk_filter)
    history = qs[:limit].values(
        'id', 'item_name', 'item_type', 'risk_level',
        'confidence', 'allergens_found', 'matched_allergens',
        'alternatives', 'created_at'
    )
    return Response({'total': qs.count(), 'history': list(history)})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_history(request):
    count, _ = PredictionHistory.objects.filter(user=request.user).delete()
    return Response({'message': f'Deleted {count} records'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_medicine_history(request):
    count, _ = MedicineCheckHistory.objects.filter(user=request.user).delete()
    return Response({'message': f'Deleted {count} medicine records'})


# ═══════════════════════════════════════════
# DASHBOARD SUMMARY
# ═══════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Get a full summary of user's SafeBite activity."""
    profile, _ = UserAllergyProfile.objects.get_or_create(user=request.user)

    return Response({
        'username': request.user.username,
        'total_allergies': profile.allergies.count(),
        'total_food_checks': PredictionHistory.objects.filter(user=request.user).count(),
        'total_medicine_checks': MedicineCheckHistory.objects.filter(user=request.user).count(),
        'total_interaction_checks': DrugInteractionHistory.objects.filter(user=request.user).count(),
        'total_symptom_logs': SymptomLog.objects.filter(user=request.user).count(),
        'high_risk_foods': PredictionHistory.objects.filter(user=request.user, risk_level='high').count(),
        'high_risk_medicines': MedicineCheckHistory.objects.filter(user=request.user, risk_level='high').count(),
        'recent_symptoms': SymptomLog.objects.filter(user=request.user).values(
            'symptoms', 'overall_severity', 'created_at'
        )[:3],
    })
