"""
SafeBite Medicine Module
- Medicine allergen checker
- Drug-drug interaction checker  
- Symptom analyzer
- Alternative medicine suggester
"""
import pandas as pd
from pathlib import Path
from difflib import get_close_matches

BASE_DIR = Path(__file__).resolve().parent

# Load medicine database
try:
    medicine_db = pd.read_csv(BASE_DIR / "medicine_database.csv")
except:
    medicine_db = pd.DataFrame()


# ─────────────────────────────────────────
# MEDICINE ALLERGEN DATABASE
# ─────────────────────────────────────────
MEDICINE_ALLERGENS = {
    "penicillin":   ["penicillin", "amoxicillin", "ampicillin", "methicillin", "oxacillin"],
    "nsaid":        ["ibuprofen", "aspirin", "naproxen", "diclofenac", "loxoprofen", "celecoxib"],
    "sulfa":        ["sulfamethoxazole", "sulfonamide", "sulfadiazine"],
    "opioid":       ["codeine", "tramadol", "morphine", "oxycodone", "hydrocodone"],
    "lactose":      ["lactose", "milk sugar"],
    "gelatin":      ["gelatin"],
    "quinolone":    ["ciprofloxacin", "levofloxacin", "moxifloxacin"],
    "macrolide":    ["erythromycin", "azithromycin", "clarithromycin"],
    "salicylate":   ["aspirin", "acetylsalicylic", "salicylate"],
    "cephalosporin":["cephalexin", "cefuroxime", "ceftriaxone"],
    "tetracycline": ["tetracycline", "doxycycline", "minocycline"],
}

# Alternative medicines by drug class
MEDICINE_ALTERNATIVES = {
    "NSAID":                    ["Paracetamol/Acetaminophen", "Tramadol (consult doctor)"],
    "Penicillin Antibiotic":    ["Azithromycin", "Erythromycin", "Ciprofloxacin (consult doctor)"],
    "Macrolide Antibiotic":     ["Ciprofloxacin", "Doxycycline (consult doctor)"],
    "Fluoroquinolone Antibiotic":["Amoxicillin", "Azithromycin (consult doctor)"],
    "Sulfonamide Antibiotic":   ["Ciprofloxacin", "Amoxicillin (consult doctor)"],
    "Opioid Analgesic":         ["Paracetamol", "Ibuprofen", "Tramadol (consult doctor)"],
    "Antihistamine":            ["Levocetirizine", "Loratadine", "Fexofenadine"],
    "Benzodiazepine":           ["Hydroxyzine", "Buspirone (consult doctor)"],
}

# Symptom to possible allergen/condition mapping
SYMPTOM_ANALYSIS = {
    "hives":            {"possible_allergens": ["peanuts", "shellfish", "dairy", "eggs", "penicillin"], "severity": "moderate"},
    "swelling":         {"possible_allergens": ["peanuts", "shellfish", "nsaid", "penicillin"], "severity": "severe"},
    "rash":             {"possible_allergens": ["penicillin", "sulfa", "nsaid", "latex"], "severity": "moderate"},
    "itching":          {"possible_allergens": ["peanuts", "dairy", "soy", "penicillin", "nsaid"], "severity": "mild"},
    "breathing":        {"possible_allergens": ["peanuts", "shellfish", "latex", "nsaid"], "severity": "severe"},
    "anaphylaxis":      {"possible_allergens": ["peanuts", "shellfish", "penicillin", "latex"], "severity": "critical"},
    "nausea":           {"possible_allergens": ["dairy", "gluten", "opioid", "nsaid"], "severity": "mild"},
    "vomiting":         {"possible_allergens": ["shellfish", "eggs", "opioid", "nsaid"], "severity": "moderate"},
    "diarrhea":         {"possible_allergens": ["dairy", "gluten", "soy", "penicillin"], "severity": "mild"},
    "stomach pain":     {"possible_allergens": ["dairy", "gluten", "nsaid", "penicillin"], "severity": "mild"},
    "dizziness":        {"possible_allergens": ["nsaid", "opioid", "sulfa"], "severity": "moderate"},
    "headache":         {"possible_allergens": ["nsaid", "sulfa", "gluten"], "severity": "mild"},
    "throat tightness": {"possible_allergens": ["peanuts", "shellfish", "penicillin", "latex"], "severity": "severe"},
    "runny nose":       {"possible_allergens": ["dairy", "gluten", "nsaid"], "severity": "mild"},
    "watery eyes":      {"possible_allergens": ["dairy", "pollen", "latex", "nsaid"], "severity": "mild"},
    "flushing":         {"possible_allergens": ["shellfish", "nsaid", "opioid"], "severity": "mild"},
    "muscle pain":      {"possible_allergens": ["statin", "opioid"], "severity": "mild"},
    "drowsiness":       {"possible_allergens": ["opioid", "antihistamine", "benzodiazepine"], "severity": "mild"},
}


def search_medicine(medicine_name):
    """Search medicine in database by name (fuzzy matching)."""
    if medicine_db.empty:
        return None

    # Exact match first
    exact = medicine_db[
        medicine_db['medicine_name'].str.lower() == medicine_name.lower()
    ]
    if not exact.empty:
        return exact.iloc[0].to_dict()

    # Fuzzy match
    all_names = medicine_db['medicine_name'].str.lower().tolist()
    matches = get_close_matches(medicine_name.lower(), all_names, n=1, cutoff=0.6)
    if matches:
        row = medicine_db[medicine_db['medicine_name'].str.lower() == matches[0]]
        if not row.empty:
            return row.iloc[0].to_dict()

    return None


def check_medicine_allergens(medicine_name, ingredients_text, user_allergies=None):
    """
    Check if a medicine contains allergens matching user's profile.
    Returns risk assessment.
    """
    # Search in database first
    db_result = search_medicine(medicine_name)
    full_text = medicine_name.lower()

    if db_result:
        full_text += " " + str(db_result.get('ingredients', '')) + " " + str(db_result.get('allergens', ''))
        drug_class = db_result.get('drug_class', 'Unknown')
        side_effects = db_result.get('side_effects', '')
    else:
        drug_class = 'Unknown'
        side_effects = ''

    if ingredients_text:
        full_text += " " + ingredients_text.lower()

    # Detect allergens in medicine
    allergens_found = []
    for allergen, keywords in MEDICINE_ALLERGENS.items():
        if any(kw in full_text for kw in keywords):
            allergens_found.append(allergen)

    # Check against user allergies
    matched_allergens = []
    if user_allergies:
        user_lower = [a.strip().lower() for a in user_allergies]
        for allergen in allergens_found:
            if allergen in user_lower:
                matched_allergens.append(allergen)

    # Risk level
    if matched_allergens:
        risk = "high"
        confidence = 95
    elif allergens_found:
        risk = "medium"
        confidence = 65
    else:
        risk = "low"
        confidence = 90

    # Suggest alternatives
    alternatives = []
    if drug_class in MEDICINE_ALTERNATIVES and risk in ["high", "medium"]:
        alternatives = MEDICINE_ALTERNATIVES[drug_class]

    return {
        "medicine_name": medicine_name,
        "found_in_database": db_result is not None,
        "drug_class": drug_class,
        "allergens_found": allergens_found,
        "matched_your_allergies": matched_allergens,
        "risk_level": risk,
        "confidence": confidence,
        "side_effects": side_effects,
        "alternative_medicines": alternatives,
        "recommendation": (
            "🚨 HIGH RISK — This medicine may cause an allergic reaction!" if risk == "high" else
            "⚠️ MEDIUM RISK — Contains potential allergens, consult your doctor." if risk == "medium" else
            "✅ LOW RISK — No known allergens detected for your profile."
        )
    }


def check_drug_interactions(medicine_list):
    """
    Check interactions between multiple medicines.
    Returns list of dangerous interactions found.
    """
    if len(medicine_list) < 2:
        return {"error": "Please provide at least 2 medicines to check interactions"}

    interactions_found = []
    checked_pairs = set()

    for i, med1 in enumerate(medicine_list):
        db1 = search_medicine(med1)
        if not db1:
            continue

        med1_interactions = str(db1.get('interactions', '')).lower().split(', ')

        for j, med2 in enumerate(medicine_list):
            if i == j:
                continue

            pair = tuple(sorted([med1.lower(), med2.lower()]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            db2 = search_medicine(med2)
            generic2 = str(db2.get('generic_name', med2)).lower() if db2 else med2.lower()
            name2_lower = med2.lower()

            # Check if med2 is in med1's interaction list
            if any(name2_lower in interaction or generic2 in interaction
                   for interaction in med1_interactions):
                interactions_found.append({
                    "medicine_1": med1,
                    "medicine_2": med2,
                    "severity": "high",
                    "warning": f"⚠️ {med1} may interact dangerously with {med2}",
                    "advice": "Consult your doctor before taking these together"
                })

    return {
        "medicines_checked": medicine_list,
        "total_interactions": len(interactions_found),
        "interactions": interactions_found,
        "safe": len(interactions_found) == 0,
        "recommendation": (
            "✅ No dangerous interactions found between these medicines." if not interactions_found
            else f"🚨 {len(interactions_found)} dangerous interaction(s) found! Consult your doctor immediately."
        )
    }


def analyze_symptoms(symptoms_list, current_medicines=None):
    """
    Analyze symptoms to identify possible allergens or reactions.
    """
    possible_allergens = {}
    severity_scores = {"mild": 1, "moderate": 2, "severe": 3, "critical": 4}
    max_severity = "mild"

    for symptom in symptoms_list:
        symptom_lower = symptom.strip().lower()

        # Direct match
        matched_key = None
        for key in SYMPTOM_ANALYSIS:
            if key in symptom_lower or symptom_lower in key:
                matched_key = key
                break

        if matched_key:
            data = SYMPTOM_ANALYSIS[matched_key]
            sev = data['severity']

            if severity_scores.get(sev, 0) > severity_scores.get(max_severity, 0):
                max_severity = sev

            for allergen in data['possible_allergens']:
                possible_allergens[allergen] = possible_allergens.get(allergen, 0) + 1

    # Sort by frequency
    sorted_allergens = sorted(possible_allergens.items(), key=lambda x: x[1], reverse=True)
    top_allergens = [a[0] for a in sorted_allergens[:5]]

    # Check if current medicines could cause symptoms
    medicine_warnings = []
    if current_medicines:
        for med in current_medicines:
            db_result = search_medicine(med)
            if db_result:
                med_side_effects = str(db_result.get('side_effects', '')).lower()
                for symptom in symptoms_list:
                    if symptom.lower() in med_side_effects:
                        medicine_warnings.append({
                            "medicine": med,
                            "symptom": symptom,
                            "warning": f"{symptom} is a known side effect of {med}"
                        })

    return {
        "symptoms_analyzed": symptoms_list,
        "overall_severity": max_severity,
        "possible_allergens": top_allergens,
        "medicine_warnings": medicine_warnings,
        "recommendation": (
            "🚨 CRITICAL — Seek emergency medical help immediately!" if max_severity == "critical" else
            "⚠️ SEVERE — See a doctor as soon as possible." if max_severity == "severe" else
            "⚠️ MODERATE — Monitor symptoms, consider seeing a doctor." if max_severity == "moderate" else
            "ℹ️ MILD — Monitor symptoms and avoid suspected allergens."
        ),
        "next_steps": [
            "Record which foods/medicines you took before symptoms appeared",
            "Avoid suspected allergens until confirmed",
            "Consult an allergist for proper testing",
            "Keep antihistamines available if prescribed"
        ] if max_severity in ["moderate", "severe"] else [
            "Monitor symptoms over the next 24 hours",
            "Stay hydrated and rest",
            "Avoid suspected allergens"
        ]
    }
