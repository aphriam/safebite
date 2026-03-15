"""
BiteCheck — Personalised ML Model v4
======================================
Allergens detected purely from keyword dictionary.
Risk calculated from user's personal profile at runtime.
"""

import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ─── LOAD MODEL ──────────────────────────────────────────────
_data              = joblib.load(BASE_DIR / "allergy_model.pkl")
_allergen_keywords = _data['allergen_keywords']
_alternatives      = _data['alternatives']

# ─── LOAD USDA ALLERGENS ──────────────────────────────────────
try:
    import json as _json
    with open(BASE_DIR / "usda_allergens.json") as _f:
        _usda = _json.load(_f)
    for _k, _v in _usda.items():
        if _k in _allergen_keywords:
            existing = _allergen_keywords[_k]
            _allergen_keywords[_k] = existing + [w for w in _v if w not in existing]
        else:
            _allergen_keywords[_k] = _v
    print(f"[BiteCheck] USDA allergens loaded into ml_model: {len(_allergen_keywords)} categories")
except:
    pass

# ─── LOAD USDA FOOD ALTERNATIVES ─────────────────────────────
try:
    with open(BASE_DIR / "usda_food_alternatives.json") as _f:
        _usda_alts = _json.load(_f)
    _alternatives.update(_usda_alts)
    print(f"[BiteCheck] USDA food alternatives loaded: {len(_alternatives)} allergens")
except:
    pass


# ─── DETECT ALLERGENS ────────────────────────────────────────
def detect_allergens(item_name, ingredients):
    """Detect allergens purely from keyword matching."""
    text = f"{str(item_name).lower()} {str(ingredients).lower()}"
    return [allergen for allergen, keywords in _allergen_keywords.items()
            if any(kw in text for kw in keywords)]


# ─── MAIN PREDICT FUNCTION ───────────────────────────────────
def predict_risk(ingredient_text, user_allergies=None, item_name=''):
    """
    Personalised risk prediction.
    HIGH   → allergen matches user's profile
    MEDIUM → food has allergens but none match user's profile
    LOW    → no allergens detected
    """

    # Step 1: Detect allergens from ingredients
    allergens_detected = detect_allergens(item_name, ingredient_text)

    # Step 2: Match against user's personal profile
    matched = []
    if user_allergies:
        user_lower = [a.strip().lower() for a in user_allergies]
        for detected in allergens_detected:
            for user_allergen in user_lower:
                if (detected == user_allergen or
                        detected in user_allergen or
                        user_allergen in detected):
                    if detected not in matched:
                        matched.append(detected)
                    break

    # Step 3: Personalised risk decision
    if not user_allergies:
        risk       = 'medium' if allergens_detected else 'low'
        confidence = 40
        recommendation = (
            "⚠️ Please set up your allergy profile for personalised results! "
            + (f"This item contains: {', '.join(allergens_detected)}"
               if allergens_detected else "No common allergens detected.")
        )

    elif matched:
        risk       = 'high'
        confidence = min(75 + len(matched) * 10, 100)
        recommendation = (
            f"🚨 AVOID! This contains {', '.join(matched)} "
            f"which you are allergic to."
        )

    elif allergens_detected:
        risk       = 'medium'
        confidence = 65
        recommendation = (
            f"⚠️ CAUTION — Contains {', '.join(allergens_detected)}. "
            f"Not in your allergy profile, but verify your profile is complete."
        )

    else:
        risk       = 'low'
        confidence = 90
        recommendation = "✅ SAFE — No known allergens detected."

    # Step 4: Safer alternatives
    alternatives = []
    for allergen in (matched or allergens_detected):
        if allergen in _alternatives:
            alternatives.append({
                'allergen':    allergen,
                'alternative': _alternatives[allergen]
            })

    return {
        'risk':                   risk,
        'confidence':             confidence,
        'confidence_percent':     f"{confidence}%",
        'allergens_detected':     allergens_detected,
        'matched_your_allergies': matched,
        'recommendation':         recommendation,
        'safer_alternatives':     alternatives,
        'is_personalised':        True,
        # Legacy keys for views.py compatibility
        'ml_prediction':          risk,
        'ml_confidence':          confidence,
        'allergens_found':        allergens_detected,
        'matched_allergens':      matched,
        'alternatives':           alternatives,
        'risk_level':             risk,
    }
