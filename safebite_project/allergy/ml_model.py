import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
model = joblib.load(BASE_DIR / "allergy_model.pkl")

def predict_risk(ingredient_text, user_allergies=None):

    probability = model.predict_proba([ingredient_text])[0][1] * 100

    # Personalization boost
    if user_allergies:
        ingredient_text_lower = ingredient_text.lower()

        for allergy in user_allergies:
            if allergy.strip().lower() in ingredient_text_lower:
                probability += 15   # increase risk if user allergen found

    probability = min(probability, 100)

    if probability > 70:
        risk = "High"
    elif probability > 40:
        risk = "Medium"
    else:
        risk = "Low"

    return risk, round(probability, 2)