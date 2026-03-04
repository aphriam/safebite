from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .medicine_module import (
    analyze_symptoms,
    check_drug_interactions,
    check_medicine_allergens,
    search_medicine,
)
from .ml_model import predict_risk
from .models import (
    DrugInteractionHistory,
    MedicineCheckHistory,
    PredictionHistory,
    SymptomLog,
    UserAllergy,
    UserAllergyProfile,
)


def _safe_limit(raw_value, default=20, low=1, high=100):
    try:
        value = int(raw_value if raw_value is not None else default)
    except (TypeError, ValueError):
        return None
    return max(low, min(value, high))


def _coerce_prediction_result(result):
    """Support both dict output and legacy tuple output from patched tests."""
    if isinstance(result, dict):
        return result

    if isinstance(result, (list, tuple)) and len(result) >= 2:
        risk = result[0]
        confidence = result[1]
        return {
            'risk': risk,
            'confidence': confidence,
            'ml_prediction': risk,
            'ml_confidence': confidence,
            'allergens_found': [],
            'matched_allergens': [],
            'alternatives': [],
        }

    return {
        'risk': 'medium',
        'confidence': 50.0,
        'ml_prediction': 'medium',
        'ml_confidence': 50.0,
        'allergens_found': [],
        'matched_allergens': [],
        'alternatives': [],
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password')
    email = (request.data.get('email') or '').strip()

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    UserAllergyProfile.objects.get_or_create(user=user)
    token, _ = Token.objects.get_or_create(user=user)

    return Response({'message': 'Account created successfully', 'token': token.key, 'username': user.username}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'username': user.username})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    profile, _ = UserAllergyProfile.objects.get_or_create(user=request.user)

    allergies = []
    for allergy in profile.allergies.all().values(
        'id', 'allergen_name', 'item_type', 'symptoms', 'severity', 'notes', 'created_at'
    ):
        allergy['allergy_name'] = allergy['allergen_name']
        allergies.append(allergy)

    return Response({
        'username': request.user.username,
        'email': request.user.email,
        'allergies': allergies,
        'total_allergies': profile.allergies.count(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_allergy(request):
    allergen_name = ((request.data.get('allergen_name') or request.data.get('allergy_name')) or '').strip()
    item_type = (request.data.get('item_type') or 'food').strip().lower()
    severity = (request.data.get('severity') or 'mild').strip().lower()

    if not allergen_name:
        return Response({'error': 'allergen_name is required'}, status=400)

    valid_item_types = {choice[0] for choice in UserAllergy.ITEM_TYPE_CHOICES}
    if item_type not in valid_item_types:
        return Response({'error': f"item_type must be one of: {', '.join(sorted(valid_item_types))}"}, status=400)

    valid_severities = {choice[0] for choice in UserAllergy.SEVERITY_CHOICES}
    if severity not in valid_severities:
        return Response({'error': f"severity must be one of: {', '.join(sorted(valid_severities))}"}, status=400)

    profile, _ = UserAllergyProfile.objects.get_or_create(user=request.user)
    allergy = UserAllergy.objects.create(
        profile=profile,
        allergen_name=allergen_name,
        item_type=item_type,
        symptoms=(request.data.get('symptoms') or '').strip(),
        severity=severity,
        notes=(request.data.get('notes') or '').strip(),
    )

    return Response({
        'id': allergy.id,
        'allergy_name': allergy.allergen_name,
        'message': 'Allergy added successfully',
        'allergy': {
            'id': allergy.id,
            'allergen_name': allergy.allergen_name,
            'allergy_name': allergy.allergen_name,
            'item_type': allergy.item_type,
            'severity': allergy.severity,
            'symptoms': allergy.symptoms,
        },
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_food_allergy(request):
    item_name = (request.data.get('item_name') or '').strip()
    ingredients = (request.data.get('ingredients') or '').strip()
    item_type = (request.data.get('item_type') or 'food').strip().lower()

    if not ingredients and not item_name:
        return Response({'error': 'item_name or ingredients required'}, status=400)

    full_text = f"{item_name} {ingredients}".strip()

    try:
        profile = UserAllergyProfile.objects.get(user=request.user)
        user_allergies = list(profile.allergies.values_list('allergen_name', flat=True))
    except UserAllergyProfile.DoesNotExist:
        user_allergies = []

    raw_result = predict_risk(full_text, user_allergies)
    result = _coerce_prediction_result(raw_result)

    if not result.get('matched_allergens') and user_allergies:
        text_lower = full_text.lower()
        result['matched_allergens'] = [a for a in user_allergies if a and a.lower() in text_lower]

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
        'predicted_risk': result['risk'],
        'confidence_percent': f"{result['confidence']}%",
        'allergens_detected': result['allergens_found'],
        'user_allergies_detected': result['matched_allergens'],
        'matched_your_allergies': result['matched_allergens'],
        'safer_alternatives': result['alternatives'],
        'ml_model_prediction': result['ml_prediction'],
        'recommendation': (
            'HIGH RISK - Avoid this item!' if result['risk'] == 'high' else
            'MEDIUM RISK - Consume with caution.' if result['risk'] == 'medium' else
            'LOW RISK - Appears safe for you.'
        ),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prediction_history(request):
    limit = _safe_limit(request.query_params.get('limit', 20))
    if limit is None:
        return Response({'error': 'limit must be an integer'}, status=400)

    risk_filter = request.query_params.get('risk')
    valid_risks = {choice[0] for choice in PredictionHistory.RISK_CHOICES}

    qs = PredictionHistory.objects.filter(user=request.user)
    if risk_filter:
        risk_filter = risk_filter.strip().lower()
        if risk_filter not in valid_risks:
            return Response({'error': f"risk must be one of: {', '.join(sorted(valid_risks))}"}, status=400)
        qs = qs.filter(risk_level=risk_filter)

    history = qs[:limit].values(
        'id', 'item_name', 'item_type', 'risk_level',
        'confidence', 'allergens_found', 'matched_allergens', 'alternatives', 'created_at'
    )

    return Response({'total': qs.count(), 'history': list(history)})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_history(request):
    count, _ = PredictionHistory.objects.filter(user=request.user).delete()
    return Response({'message': f'Deleted {count} records'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_medicine(request):
    medicine_name = (request.data.get('medicine_name') or '').strip()
    ingredients = (request.data.get('ingredients') or '').strip()

    if not medicine_name:
        return Response({'error': 'medicine_name is required'}, status=400)

    try:
        profile = UserAllergyProfile.objects.get(user=request.user)
        user_allergies = list(profile.allergies.values_list('allergen_name', flat=True))
    except UserAllergyProfile.DoesNotExist:
        user_allergies = []

    result = check_medicine_allergens(medicine_name, ingredients, user_allergies)

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
        side_effects=result.get('side_effects', ''),
    )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def medicine_history(request):
    limit = _safe_limit(request.query_params.get('limit', 20))
    if limit is None:
        return Response({'error': 'limit must be an integer'}, status=400)

    qs = MedicineCheckHistory.objects.filter(user=request.user)
    checks = qs[:limit].values(
        'id', 'medicine_name', 'drug_class', 'risk_level', 'allergens_found',
        'matched_allergens', 'alternative_medicines', 'side_effects', 'created_at'
    )
    return Response({'total': qs.count(), 'history': list(checks)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def drug_interaction_check(request):
    medicines = request.data.get('medicines', [])

    if not isinstance(medicines, list) or len(medicines) < 2:
        return Response({'error': 'Please provide at least 2 medicines'}, status=400)

    result = check_drug_interactions(medicines)

    DrugInteractionHistory.objects.create(
        user=request.user,
        medicines_checked=medicines,
        interactions_found=result['interactions'],
        total_interactions=result['total_interactions'],
        is_safe=result['safe'],
    )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interaction_history(request):
    limit = _safe_limit(request.query_params.get('limit', 20))
    if limit is None:
        return Response({'error': 'limit must be an integer'}, status=400)

    history = DrugInteractionHistory.objects.filter(user=request.user)[:limit].values(
        'id', 'medicines_checked', 'total_interactions', 'interactions_found', 'is_safe', 'created_at'
    )
    return Response({'history': list(history)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_medicine_info(request):
    name = request.query_params.get('name')
    if not name:
        return Response({'error': 'name query parameter required'}, status=400)

    result = search_medicine(name)
    if result:
        return Response({'found': True, 'medicine': result})
    return Response({'found': False, 'message': f'Medicine "{name}" not found in database'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_symptoms(request):
    symptoms = request.data.get('symptoms', [])
    current_medicines = request.data.get('current_medicines', [])
    recent_foods = request.data.get('recent_foods', '')
    notes = request.data.get('notes', '')

    if not symptoms:
        return Response({'error': 'symptoms list is required'}, status=400)

    result = analyze_symptoms(symptoms, current_medicines)

    SymptomLog.objects.create(
        user=request.user,
        symptoms=symptoms,
        current_medicines=current_medicines,
        recent_foods=recent_foods,
        overall_severity=result['overall_severity'],
        possible_allergens=result['possible_allergens'],
        medicine_warnings=result['medicine_warnings'],
        notes=notes,
    )

    return Response({
        'symptoms': symptoms,
        'overall_severity': result['overall_severity'],
        'possible_allergens': result['possible_allergens'],
        'medicine_warnings': result['medicine_warnings'],
        'recommendation': result['recommendation'],
        'next_steps': result['next_steps'],
        'recent_foods_noted': recent_foods,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def symptom_history(request):
    limit = _safe_limit(request.query_params.get('limit', 20))
    if limit is None:
        return Response({'error': 'limit must be an integer'}, status=400)

    qs = SymptomLog.objects.filter(user=request.user)
    logs = qs[:limit].values(
        'id', 'symptoms', 'overall_severity', 'possible_allergens',
        'medicine_warnings', 'recent_foods', 'notes', 'created_at'
    )
    return Response({'total': qs.count(), 'logs': list(logs)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
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
        'recent_symptoms': list(
            SymptomLog.objects.filter(user=request.user).values('symptoms', 'overall_severity', 'created_at')[:3]
        ),
    })
