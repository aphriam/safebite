"""
BiteCheck — Symptom Analyser
==============================
Fully personalised symptom analysis.
Uses Kaggle symptom dataset + SIDER data when available.

Data sources:
  - symptom_data.json   → from Kaggle (convert_symptoms.py)
  - sider_data.json     → from SIDER database (fetch_sider_data.py)
"""

import json
from pathlib import Path
from .medicine_search import search_medicine
from .medicine_checker import detect_allergens

BASE_DIR = Path(__file__).resolve().parent

# ─── LOAD KAGGLE SYMPTOM DATA ────────────────────────────────
_kaggle_symptoms = {}
try:
    with open(BASE_DIR / "symptom_data.json") as f:
        data = json.load(f)
        _kaggle_symptoms = data.get("symptom_hints", {})
    print(f"[BiteCheck] Loaded {len(_kaggle_symptoms)//2} symptoms from Kaggle")
except:
    print("[BiteCheck] symptom_data.json not found")

# ─── LOAD SIDER DATA ─────────────────────────────────────────
_sider_data = {}
try:
    with open(BASE_DIR / "sider_data.json") as f:
        _sider_data = json.load(f)
    print(f"[BiteCheck] Loaded SIDER symptom-drug data")
except:
    pass

# ─── BUILT-IN SYMPTOM HINTS (fallback) ───────────────────────
BUILTIN_SYMPTOM_HINTS = {
    'hives':               {'allergens': ['peanuts', 'shellfish', 'dairy', 'eggs', 'penicillin'], 'severity': 'moderate'},
    'urticaria':           {'allergens': ['peanuts', 'shellfish', 'dairy', 'eggs', 'penicillin'], 'severity': 'moderate'},
    'rash':                {'allergens': ['penicillin', 'sulfa', 'nsaid', 'latex'], 'severity': 'moderate'},
    'itching':             {'allergens': ['peanuts', 'dairy', 'soy', 'penicillin', 'nsaid'], 'severity': 'mild'},
    'swelling':            {'allergens': ['peanuts', 'shellfish', 'nsaid', 'penicillin'], 'severity': 'severe'},
    'breathing':           {'allergens': ['peanuts', 'shellfish', 'latex', 'nsaid'], 'severity': 'severe'},
    'breathlessness':      {'allergens': ['peanuts', 'shellfish', 'latex', 'nsaid'], 'severity': 'severe'},
    'wheezing':            {'allergens': ['peanuts', 'shellfish', 'nsaid', 'latex'], 'severity': 'severe'},
    'anaphylaxis':         {'allergens': ['peanuts', 'shellfish', 'penicillin', 'latex'], 'severity': 'critical'},
    'nausea':              {'allergens': ['dairy', 'gluten', 'opioid', 'nsaid'], 'severity': 'mild'},
    'vomiting':            {'allergens': ['shellfish', 'eggs', 'opioid', 'nsaid'], 'severity': 'moderate'},
    'diarrhea':            {'allergens': ['dairy', 'gluten', 'soy', 'penicillin'], 'severity': 'mild'},
    'diarrhoea':           {'allergens': ['dairy', 'gluten', 'soy', 'penicillin'], 'severity': 'mild'},
    'stomach pain':        {'allergens': ['dairy', 'gluten', 'nsaid', 'penicillin'], 'severity': 'mild'},
    'headache':            {'allergens': ['nsaid', 'sulfa', 'gluten', 'sulfites', 'dairy'], 'severity': 'mild'},
    'dizziness':           {'allergens': ['nsaid', 'opioid', 'sulfa'], 'severity': 'moderate'},
    'throat tightness':    {'allergens': ['peanuts', 'shellfish', 'penicillin', 'latex'], 'severity': 'severe'},
    'runny nose':          {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
    'watery eyes':         {'allergens': ['dairy', 'latex', 'nsaid'], 'severity': 'mild'},
    'chest pain':          {'allergens': ['peanuts', 'shellfish', 'nsaid', 'latex'], 'severity': 'severe'},
    'flushing':            {'allergens': ['shellfish', 'nsaid', 'opioid', 'sulfites'], 'severity': 'mild'},
    'muscle pain':         {'allergens': ['nsaid', 'opioid', 'statin'], 'severity': 'mild'},
    'joint pain':          {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
    'fatigue':             {'allergens': ['dairy', 'gluten', 'soy'], 'severity': 'mild'},
    'bloating':            {'allergens': ['dairy', 'gluten', 'soy'], 'severity': 'mild'},
    'eczema':              {'allergens': ['dairy', 'eggs', 'gluten', 'soy'], 'severity': 'moderate'},
    'fever':               {'allergens': ['penicillin', 'sulfa', 'nsaid'], 'severity': 'moderate'},
    'lip swelling':        {'allergens': ['peanuts', 'shellfish', 'penicillin'], 'severity': 'severe'},
    'tongue swelling':     {'allergens': ['peanuts', 'shellfish', 'penicillin', 'nsaid'], 'severity': 'severe'},
    'constipation':        {'allergens': ['dairy', 'opioid'], 'severity': 'mild'},
    'cramps':              {'allergens': ['dairy', 'gluten', 'soy'], 'severity': 'mild'},
    'sneezing':            {'allergens': ['dairy', 'gluten'], 'severity': 'mild'},
    'cough':               {'allergens': ['dairy', 'gluten', 'nsaid', 'ace_inhibitor'], 'severity': 'mild'},
    'skin rash':           {'allergens': ['penicillin', 'sulfa', 'nsaid', 'latex'], 'severity': 'moderate'},
    'palpitations':        {'allergens': ['dairy', 'gluten', 'sulfites'], 'severity': 'moderate'},
    'anxiety':             {'allergens': ['gluten', 'dairy'], 'severity': 'mild'},
    'depression':          {'allergens': ['gluten', 'dairy'], 'severity': 'mild'},
    'brain fog':           {'allergens': ['gluten', 'dairy'], 'severity': 'mild'},
    'mouth tingling':      {'allergens': ['peanuts', 'tree nuts', 'shellfish'], 'severity': 'moderate'},
    'dark urine':          {'allergens': ['penicillin', 'sulfa', 'nsaid'], 'severity': 'moderate'},
    'back pain':           {'allergens': ['nsaid', 'dairy', 'gluten'], 'severity': 'mild'},
    'loss of appetite':    {'allergens': ['dairy', 'gluten', 'opioid'], 'severity': 'mild'},
    'weight loss':         {'allergens': ['gluten', 'dairy'], 'severity': 'mild'},
    'indigestion':         {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
    'acidity':             {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
    'drowsiness':          {'allergens': ['opioid', 'nsaid'], 'severity': 'mild'},
    'insomnia':            {'allergens': ['gluten', 'dairy', 'nsaid'], 'severity': 'mild'},
}

SEVERITY_SCORE = {'mild': 1, 'moderate': 2, 'severe': 3, 'critical': 4}


def get_symptom_data(symptom):
    """
    Get allergens and severity for a symptom.
    Checks Kaggle data first, then SIDER, then built-in hints.
    """
    symptom_lower = symptom.strip().lower()
    symptom_under = symptom_lower.replace(' ', '_')

    # Check Kaggle data
    for key in [symptom_lower, symptom_under]:
        if key in _kaggle_symptoms:
            return _kaggle_symptoms[key]

    # Check SIDER data
    if symptom_lower in _sider_data:
        return _sider_data[symptom_lower]

    # Partial match in Kaggle
    for key in _kaggle_symptoms:
        if symptom_lower in key or key in symptom_lower:
            return _kaggle_symptoms[key]

    # Built-in fallback
    for key in BUILTIN_SYMPTOM_HINTS:
        if key in symptom_lower or symptom_lower in key:
            return BUILTIN_SYMPTOM_HINTS[key]

    return None


def analyze_symptoms(symptoms_list, current_medicines=None,
                     recent_foods='', user_allergies=None):
    """
    Fully personalised symptom analysis.

    Steps:
    1. Match symptoms → allergen hints (Kaggle + SIDER + built-in)
    2. Detect allergens in recent foods
    3. Cross-match with user's allergy profile
    4. Check medicine side effects
    5. Return personalised results
    """
    max_severity   = 'mild'
    allergen_votes = {}
    confirmed      = []
    food_allergens = []

    user_lower = [a.strip().lower() for a in (user_allergies or [])]

    # Step 1: Score allergens from symptoms
    for symptom in symptoms_list:
        data = get_symptom_data(symptom)
        if data:
            sev = data.get('severity', 'mild')
            if SEVERITY_SCORE.get(sev, 0) > SEVERITY_SCORE.get(max_severity, 0):
                max_severity = sev
            for allergen in data.get('allergens', []):
                allergen_votes[allergen] = allergen_votes.get(allergen, 0) + 1

    # Step 2: Detect allergens in recent foods
    if recent_foods and recent_foods.strip():
        food_allergens = detect_allergens(recent_foods)
        for allergen in food_allergens:
            allergen_votes[allergen] = allergen_votes.get(allergen, 0) + 2

    # Step 3: Cross-match with user profile
    for allergen in list(allergen_votes.keys()):
        for ua in user_lower:
            if allergen == ua or allergen in ua or ua in allergen:
                if allergen not in confirmed:
                    confirmed.append(allergen)
                allergen_votes[allergen] = allergen_votes.get(allergen, 0) + 5
                break

    # Step 4: Check medicine side effects
    medicine_warnings = []
    if current_medicines:
        for med in current_medicines:
            db = search_medicine(med)
            if db:
                effects = str(db.get('side_effects', '')).lower()
                for symptom in symptoms_list:
                    if symptom.strip().lower() in effects:
                        medicine_warnings.append({
                            'medicine': med,
                            'symptom':  symptom,
                            'warning':  f'{symptom} is a known side effect of {med}'
                        })

    # Sort allergens by vote score
    top_allergens = [a for a, _ in sorted(
        allergen_votes.items(), key=lambda x: x[1], reverse=True
    )][:5]

    # Build recommendation
    if confirmed:
        cause = f'Your known allergen(s) {", ".join(confirmed)} may have triggered these symptoms.'
    elif food_allergens:
        cause = f'Recent foods contained: {", ".join(food_allergens)}.'
    elif top_allergens:
        cause = f'Possible triggers: {", ".join(top_allergens[:3])}.'
    else:
        cause = 'Could not identify a specific allergen trigger.'

    if max_severity == 'critical':
        recommendation = f'🚨 CRITICAL — Seek emergency help immediately! {cause}'
    elif max_severity == 'severe':
        recommendation = f'⚠️ SEVERE — See a doctor as soon as possible. {cause}'
    elif max_severity == 'moderate':
        recommendation = f'⚠️ MODERATE — Monitor symptoms, consider seeing a doctor. {cause}'
    else:
        recommendation = f'ℹ️ MILD — Monitor symptoms and avoid suspected allergens. {cause}'

    # Next steps
    if confirmed:
        next_steps = [
            f'Avoid {", ".join(confirmed)} — these match your allergy profile',
            'Take your prescribed antihistamine if available',
            'See a doctor if symptoms worsen',
            'Update your allergy profile if new allergens are confirmed',
        ]
    elif max_severity in ['severe', 'critical']:
        next_steps = [
            'Seek emergency medical help immediately',
            'Use your EpiPen if prescribed',
            'Record everything you ate/took in the last 2 hours',
            'Do not take any new medicines without doctor advice',
        ]
    else:
        next_steps = [
            'Record which foods/medicines you had before symptoms started',
            'Avoid suspected allergens until confirmed',
            'Consult an allergist for proper allergy testing',
            'Keep antihistamines available if prescribed',
        ]

    return {
        'symptoms_analyzed':      symptoms_list,
        'overall_severity':       max_severity,
        'possible_allergens':     top_allergens,
        'confirmed_from_profile': confirmed,
        'allergens_in_foods':     food_allergens,
        'medicine_warnings':      medicine_warnings,
        'recommendation':         recommendation,
        'next_steps':             next_steps,
        'data_sources': {
            'symptoms': 'Kaggle' if _kaggle_symptoms else 'Built-in',
            'sider':    'Loaded' if _sider_data else 'Not loaded',
        }
    }
