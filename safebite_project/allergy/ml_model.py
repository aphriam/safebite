"""
SafeBite ML Model
Hybrid approach: Allergen keyword matching + TF-IDF Random Forest
"""
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "allergy_model.pkl"

# Load trained model, but keep service alive even if the artifact is missing/corrupt.
try:
    model = joblib.load(MODEL_PATH)
except Exception:
    model = None

# -----------------------------------------
# ALLERGEN KEYWORD DATABASE
# -----------------------------------------
ALLERGEN_KEYWORDS = {
    "peanuts":    ["peanut", "groundnut", "arachis"],
    "tree nuts":  ["almond", "cashew", "walnut", "pistachio", "hazelnut",
                   "macadamia", "pecan", "brazil nut", "pine nut"],
    "shellfish":  ["shrimp", "prawn", "crab", "lobster", "crayfish",
                   "scallop", "clam", "oyster", "mussel"],
    "fish":       ["fish", "salmon", "tuna", "cod", "tilapia", "anchovy",
                   "sardine", "halibut", "trout", "mackerel"],
    "dairy":      ["milk", "cream", "butter", "cheese", "yogurt",
                   "whey", "lactose", "casein", "ghee"],
    "eggs":       ["egg", "albumin", "mayonnaise", "mayo", "meringue"],
    "gluten":     ["wheat", "flour", "gluten", "bread", "pasta", "rye",
                   "barley", "spelt", "semolina", "oat", "cereal"],
    "soy":        ["soy", "soya", "tofu", "tempeh", "edamame", "miso"],
    "sesame":     ["sesame", "tahini"],
    "penicillin": ["penicillin", "amoxicillin", "ampicillin"],
    "nsaid":      ["ibuprofen", "aspirin", "naproxen", "loxoprofen"],
    "sulfa":      ["sulfa", "sulfamethoxazole"],
    "latex":      ["latex", "rubber"],
}

# Safe alternatives for common allergens
ALTERNATIVES = {
    "peanuts":    "Sunflower seed butter, pumpkin seed butter",
    "tree nuts":  "Sunflower seeds, pumpkin seeds, hemp seeds",
    "shellfish":  "White fish, tofu, chicken",
    "fish":       "Chicken, tofu, lentils, chickpeas",
    "dairy":      "Oat milk, coconut milk, almond milk, soy milk",
    "eggs":       "Flax egg, chia egg, aquafaba",
    "gluten":     "Rice flour, almond flour, corn tortilla, rice pasta",
    "soy":        "Coconut aminos, chickpeas, lentils",
    "sesame":     "Pumpkin seed oil, flaxseed",
    "penicillin": "Consult your doctor for alternative antibiotics",
    "nsaid":      "Paracetamol/Acetaminophen (consult doctor)",
    "sulfa":      "Consult your doctor for alternatives",
    "latex":      "Nitrile or vinyl gloves",
}


def detect_allergens(text):
    """Return list of allergens found in text."""
    text_lower = text.lower()
    found = []
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(allergen)
    return found


def predict_risk(ingredient_text, user_allergies=None):
    """
    Hybrid risk prediction combining:
    1. ML model (TF-IDF + Random Forest)
    2. Allergen keyword detection
    3. Personal allergy profile matching

    Returns:
        risk (str): 'high', 'medium', or 'low'
        confidence (float): 0-100
        allergens_found (list): allergens detected in text
        matched_allergens (list): allergens matching user profile
        alternatives (list): suggested safer alternatives
    """

    # Step 1: ML Prediction (fallback when model is unavailable)
    if model is not None:
        ml_pred = model.predict([ingredient_text])[0]
        ml_proba = model.predict_proba([ingredient_text])[0]
        ml_confidence = round(max(ml_proba) * 100, 1)
    else:
        ml_pred = "medium"
        ml_confidence = 0.0

    # Step 2: Allergen detection
    allergens_found = detect_allergens(ingredient_text)

    # Step 3: Personal allergy matching
    matched_allergens = []
    personal_boost = 0
    if user_allergies:
        user_lower = [a.strip().lower() for a in user_allergies]
        for allergen in allergens_found:
            if allergen in user_lower:
                matched_allergens.append(allergen)
                personal_boost += 30

    # Step 4: Compute hybrid score
    base_score = {"high": 85, "medium": 50, "low": 15}.get(ml_pred, 50)
    allergen_boost = len(allergens_found) * 10
    final_score = min(base_score + allergen_boost + personal_boost, 100)

    # Step 5: Final risk level
    if final_score >= 70 or matched_allergens:
        risk = "high"
    elif final_score >= 40 or allergens_found:
        risk = "medium"
    else:
        risk = "low"

    # Step 6: Suggest alternatives
    suggested_alternatives = []
    for allergen in (matched_allergens or allergens_found):
        if allergen in ALTERNATIVES:
            suggested_alternatives.append({
                "allergen": allergen,
                "alternative": ALTERNATIVES[allergen]
            })

    return {
        "risk": risk,
        "confidence": round(final_score, 1),
        "ml_prediction": ml_pred,
        "ml_confidence": ml_confidence,
        "allergens_found": allergens_found,
        "matched_allergens": matched_allergens,
        "alternatives": suggested_alternatives,
    }
