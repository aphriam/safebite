"""
BiteCheck — Medicine Allergen Checker
========================================
Checks if a medicine is safe based on user's allergy profile.
Uses OpenFDA data when available, falls back to keyword detection.

Data source: OpenFDA API (fetched once by fetch_fda_data.py)
"""

import json
from pathlib import Path
from .medicine_search import search_medicine

BASE_DIR = Path(__file__).resolve().parent

# ─── LOAD OPENFDA DATA ───────────────────────────────────────
_fda_data = {}
try:
    with open(BASE_DIR / "fda_medicine_data.json") as f:
        _fda_data = json.load(f)
    print(f"[BiteCheck] Loaded {len(_fda_data)} medicines from OpenFDA")
except:
    print("[BiteCheck] fda_medicine_data.json not found — using keyword detection only")

# ─── ALLERGEN KEYWORDS ───────────────────────────────────────
ALLERGEN_KEYWORDS = {
    'peanuts':       ['peanut', 'groundnut', 'arachis'],
    'tree nuts':     ['almond', 'cashew', 'walnut', 'pistachio', 'hazelnut',
                      'macadamia', 'pecan', 'brazil nut', 'pine nut'],
    'shellfish':     ['shrimp', 'prawn', 'crab', 'lobster', 'shellfish'],
    'fish':          ['salmon', 'tuna', 'cod', 'fish sauce', 'fish stock'],
    'dairy':         ['milk', 'cream', 'butter', 'cheese', 'lactose', 'whey',
                      'casein', 'milk powder', 'milk solids'],
    'eggs':          ['egg', 'albumin', 'mayonnaise', 'meringue'],
    'gluten':        ['wheat', 'gluten', 'barley', 'rye', 'semolina'],
    'soy':           ['soy', 'soya', 'soybean', 'tofu'],
    'sesame':        ['sesame', 'tahini'],
    'corn':          ['corn starch', 'cornstarch', 'corn syrup', 'maize'],
    'gelatin':       ['gelatin', 'gelatine'],
    'latex':         ['latex', 'natural rubber'],
    'penicillin':    ['penicillin', 'amoxicillin', 'ampicillin',
                      'flucloxacillin', 'benzylpenicillin'],
    'cephalosporin': ['cephalosporin', 'cefalexin', 'cefuroxime',
                      'ceftriaxone', 'cefixime'],
    'sulfa':         ['sulfamethoxazole', 'sulfadiazine', 'sulfonamide'],
    'nsaid':         ['ibuprofen', 'naproxen', 'diclofenac', 'aspirin',
                      'indomethacin', 'celecoxib', 'mefenamic acid',
                      'acetylsalicylic acid'],
    'opioid':        ['morphine', 'codeine', 'tramadol', 'oxycodone',
                      'fentanyl', 'pethidine'],
    'quinolone':     ['ciprofloxacin', 'levofloxacin', 'norfloxacin',
                      'moxifloxacin'],
    'macrolide':     ['erythromycin', 'azithromycin', 'clarithromycin'],
    'tetracycline':  ['tetracycline', 'doxycycline', 'minocycline'],
    'ace_inhibitor': ['lisinopril', 'enalapril', 'ramipril', 'captopril'],
    'statin':        ['atorvastatin', 'simvastatin', 'rosuvastatin',
                      'pravastatin'],
}

# ─── LOAD USDA ALLERGEN KEYWORDS ────────────────────────────
try:
    with open(BASE_DIR / "usda_allergens.json") as _f:
        _usda_allergens = json.load(_f)
    for _k, _v in _usda_allergens.items():
        if _k in ALLERGEN_KEYWORDS:
            existing = ALLERGEN_KEYWORDS[_k]
            ALLERGEN_KEYWORDS[_k] = existing + [w for w in _v if w not in existing]
        else:
            ALLERGEN_KEYWORDS[_k] = _v
    print(f"[BiteCheck] Loaded {len(_usda_allergens)} allergen categories from USDA")
except:
    print("[BiteCheck] usda_allergens.json not found — using built-in keywords")

# ─── MEDICINE ALTERNATIVES ───────────────────────────────────
# Loaded from RxNorm if available, else fallback
_rxnorm_alternatives = {}
try:
    with open(BASE_DIR / "rxnorm_alternatives.json") as f:
        _rxnorm_alternatives = json.load(f)
    print(f"[BiteCheck] Loaded RxNorm alternatives for {len(_rxnorm_alternatives)} drug classes")
except:
    pass

# Fallback alternatives
FALLBACK_ALTERNATIVES = {
    'NSAID':                     ['Paracetamol/Acetaminophen (consult doctor)'],
    'Penicillin Antibiotic':     ['Azithromycin', 'Erythromycin (consult doctor)'],
    'Macrolide Antibiotic':      ['Ciprofloxacin', 'Doxycycline (consult doctor)'],
    'Fluoroquinolone Antibiotic':['Amoxicillin', 'Azithromycin (consult doctor)'],
    'Sulfonamide Antibiotic':    ['Ciprofloxacin', 'Amoxicillin (consult doctor)'],
    'Opioid Analgesic':          ['Paracetamol', 'Tramadol (consult doctor)'],
    'Antihistamine':             ['Levocetirizine', 'Loratadine', 'Fexofenadine'],
    'Antibiotic':                ['Consult doctor for class-specific alternatives'],
    'Analgesic':                 ['Paracetamol', 'Ibuprofen (if not NSAID allergic)'],
    'Antihypertensive':          ['Consult doctor for alternatives'],
    'Statin':                    ['Consult doctor for alternatives'],
    'Antidepressant':            ['Consult doctor for alternatives'],
    'Anticonvulsant':            ['Consult doctor for alternatives'],
    'Antidiabetic':              ['Consult doctor for alternatives'],
}


def detect_allergens(text):
    """Detect allergens from text using keyword dictionary."""
    text_lower = str(text).lower()
    return [a for a, kws in ALLERGEN_KEYWORDS.items()
            if any(kw in text_lower for kw in kws)]


def check_medicine_allergens(medicine_name, ingredients_text='', user_allergies=None):
    """
    Check if a medicine is safe for a specific user.

    Steps:
    1. Search medicine in local database
    2. Detect allergens using keyword matching
    3. Boost with OpenFDA data if available
    4. Match against user's medicine allergy profile
    5. Return personalised risk assessment
    """
    # Step 1: Search local database
    db_result  = search_medicine(medicine_name)
    full_text  = medicine_name.lower()
    drug_class = 'Unknown'
    side_effects = ''

    if db_result:
        full_text   += ' ' + str(db_result.get('ingredients', ''))
        drug_class   = db_result.get('drug_class', 'Unknown')
        side_effects = db_result.get('side_effects', '')

    if ingredients_text:
        full_text += ' ' + ingredients_text.lower()

    # Step 2: Keyword-based allergen detection
    allergens_found = detect_allergens(full_text)

    # Step 3: Boost with OpenFDA data
    med_lower = medicine_name.lower()
    if med_lower in _fda_data:
        fda = _fda_data[med_lower]
        for allergen in fda.get('allergens', []):
            if allergen not in allergens_found:
                allergens_found.append(allergen)
        if drug_class == 'Unknown':
            drug_class = fda.get('drug_class', 'Unknown')
        if not side_effects and fda.get('side_effects'):
            side_effects = ', '.join(fda['side_effects'])

    # Step 4: Match against user's medicine allergy profile
    matched_allergens = []
    if user_allergies:
        user_lower = [a.strip().lower() for a in user_allergies]
        for allergen in allergens_found:
            for ua in user_lower:
                if allergen == ua or allergen in ua or ua in allergen:
                    if allergen not in matched_allergens:
                        matched_allergens.append(allergen)
                    break

    # Step 5: Risk decision
    if matched_allergens:
        risk       = 'high'
        confidence = 95
    elif allergens_found:
        risk       = 'medium'
        confidence = 65
    else:
        risk       = 'low'
        confidence = 90

    # Get alternatives — RxNorm first, then fallback
    alternatives = (
        _rxnorm_alternatives.get(drug_class) or
        FALLBACK_ALTERNATIVES.get(drug_class) or
        []
    ) if risk in ['high', 'medium'] else []

    return {
        'medicine_name':          medicine_name,
        'found_in_database':      db_result is not None,
        'drug_class':             drug_class,
        'allergens_found':        allergens_found,
        'matched_your_allergies': matched_allergens,
        'risk_level':             risk,
        'confidence':             confidence,
        'side_effects':           side_effects,
        'alternative_medicines':  alternatives,
        'data_sources':           ['OpenFDA' if med_lower in _fda_data else 'Keywords',
                                   'DrugBank' if db_result else ''],
        'recommendation': (
            '🚨 HIGH RISK — This medicine may cause an allergic reaction!' if risk == 'high' else
            '⚠️ MEDIUM RISK — Contains potential allergens, consult your doctor.' if risk == 'medium' else
            '✅ LOW RISK — No known allergens detected for your profile.'
        )
    }
