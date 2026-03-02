from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UserAllergy
from .ml_model import predict_risk

@api_view(['POST'])
def predict_food_allergy(request):
    if not request.user.is_authenticated:
        return Response({"error": "Login required"}, status=401)

    ingredients = request.data.get("ingredients")
    if not ingredients:
        return Response({"error": "Ingredients required"}, status=400)

    # 1. Use .filter().first() to avoid MultipleObjectsReturned
    # This safely returns the first record found, or None if zero records exist.
    user_data = UserAllergy.objects.filter(user=request.user).first()

    # 2. Extract allergies safely
    if user_data and user_data.allergies:
        # Splits string and removes extra spaces
        user_allergies = [a.strip() for a in user_data.allergies.split(",") if a.strip()]
    else:
        user_allergies = []

    # 3. Call the ML function
    risk, probability = predict_risk(ingredients, user_allergies)

    return Response({
        "ingredients": ingredients,
        "user_allergies_detected": user_allergies,
        "predicted_risk": risk,
        "confidence_percent": f"{probability}%"
    })