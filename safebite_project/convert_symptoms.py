"""
BiteCheck — Kaggle Symptom Dataset Converter
=============================================
Converts Kaggle symptom files into BiteCheck's medicine_module.py format.

Files needed:
  - Symptom-severity.csv   → symptom weights
  - symptom_Description.csv → disease descriptions
  - dieseas symptom.csv    → disease-symptom mappings

Run: py convert_symptoms.py
"""

import pandas as pd
import json
from pathlib import Path

# ─── PATHS ───────────────────────────────────────────────────
SEVERITY_FILE    = Path(r"C:\Users\DELL\Desktop\Symptom-severity.csv")
DESCRIPTION_FILE = Path(r"C:\Users\DELL\Desktop\symptom_Description.csv")
DISEASE_FILE     = Path(r"C:\Users\DELL\Desktop\dieseas symptom.csv")
OUTPUT_FILE      = Path("allergy/symptom_data.json")

# ─── ALLERGEN HINTS PER SYMPTOM ──────────────────────────────
# Maps symptom → which allergens commonly cause it
# Based on medical literature
SYMPTOM_ALLERGEN_MAP = {
    # Skin symptoms
    'itching':               ['peanuts', 'dairy', 'soy', 'penicillin', 'nsaid', 'latex'],
    'skin_rash':             ['penicillin', 'sulfa', 'nsaid', 'latex', 'dairy', 'eggs'],
    'nodal_skin_eruptions':  ['penicillin', 'sulfa', 'nsaid'],
    'hives':                 ['peanuts', 'shellfish', 'dairy', 'eggs', 'penicillin'],
    'urticaria':             ['peanuts', 'shellfish', 'dairy', 'eggs', 'penicillin'],
    'eczema':                ['dairy', 'eggs', 'gluten', 'soy'],
    'skin_peeling':          ['nsaid', 'sulfa', 'penicillin'],
    'blister':               ['penicillin', 'sulfa', 'nsaid'],
    'red_spots_over_body':   ['penicillin', 'sulfa', 'nsaid'],
    'dischromic_patches':    ['dairy', 'gluten'],
    'pus_filled_pimples':    ['dairy', 'gluten'],
    'blackheads':            ['dairy'],
    'inflammatory_nails':    ['gluten', 'dairy'],

    # Respiratory symptoms
    'continuous_sneezing':   ['dairy', 'gluten', 'latex', 'pollen'],
    'breathlessness':        ['peanuts', 'shellfish', 'latex', 'nsaid'],
    'wheezing':              ['peanuts', 'shellfish', 'nsaid', 'latex'],
    'cough':                 ['dairy', 'gluten', 'nsaid', 'ace_inhibitor'],
    'phlegm':                ['dairy', 'gluten'],
    'mucoid_sputum':         ['dairy', 'gluten'],
    'runny_nose':            ['dairy', 'gluten', 'nsaid', 'latex'],
    'congestion':            ['dairy', 'gluten', 'nsaid'],
    'throat_irritation':     ['dairy', 'gluten', 'penicillin'],
    'sinus_pressure':        ['dairy', 'gluten'],
    'chest_pain':            ['peanuts', 'shellfish', 'nsaid', 'latex'],
    'rusty_sputum':          ['penicillin', 'sulfa'],
    'blood_in_sputum':       ['nsaid', 'penicillin'],

    # GI symptoms
    'nausea':                ['dairy', 'gluten', 'opioid', 'nsaid', 'penicillin'],
    'vomiting':              ['shellfish', 'eggs', 'opioid', 'nsaid'],
    'diarrhoea':             ['dairy', 'gluten', 'soy', 'penicillin'],
    'stomach_pain':          ['dairy', 'gluten', 'nsaid', 'penicillin'],
    'abdominal_pain':        ['dairy', 'gluten', 'nsaid'],
    'belly_pain':            ['dairy', 'gluten', 'nsaid'],
    'indigestion':           ['dairy', 'gluten', 'nsaid', 'opioid'],
    'acidity':               ['dairy', 'gluten', 'nsaid'],
    'loss_of_appetite':      ['dairy', 'gluten', 'opioid'],
    'constipation':          ['dairy', 'opioid'],
    'passage_of_gases':      ['dairy', 'gluten', 'soy'],
    'stomach_bleeding':      ['nsaid', 'aspirin'],
    'bloody_stool':          ['nsaid', 'dairy', 'gluten'],
    'distention_of_abdomen': ['dairy', 'gluten', 'soy'],
    'internal_itching':      ['dairy', 'gluten', 'penicillin'],
    'ulcers_on_tongue':      ['gluten', 'dairy'],

    # Neurological symptoms
    'headache':              ['nsaid', 'sulfa', 'gluten', 'sulfites', 'dairy'],
    'dizziness':             ['nsaid', 'opioid', 'sulfa'],
    'altered_sensorium':     ['opioid', 'nsaid'],
    'lack_of_concentration': ['gluten', 'dairy'],
    'visual_disturbances':   ['nsaid', 'sulfa'],
    'blurred_and_distorted_vision': ['nsaid', 'sulfa', 'gluten'],
    'word_finding_difficulty': ['gluten'],
    'anxiety':               ['gluten', 'dairy', 'caffeine'],
    'depression':            ['gluten', 'dairy'],
    'irritability':          ['gluten', 'dairy'],
    'mood_swings':           ['gluten', 'dairy'],
    'restlessness':          ['opioid', 'nsaid'],

    # Swelling symptoms
    'swelling_of_stomach':   ['dairy', 'gluten', 'soy'],
    'swelled_lymph_nodes':   ['penicillin', 'sulfa'],
    'pain_behind_the_eyes':  ['nsaid', 'sulfa'],
    'redness_of_eyes':       ['dairy', 'latex', 'nsaid'],
    'watering_from_eyes':    ['dairy', 'latex', 'nsaid'],
    'sunken_eyes':           ['dairy', 'gluten'],

    # Systemic symptoms
    'fatigue':               ['dairy', 'gluten', 'soy'],
    'lethargy':              ['dairy', 'gluten', 'opioid'],
    'malaise':               ['penicillin', 'sulfa', 'nsaid'],
    'weakness_in_limbs':     ['gluten', 'dairy', 'nsaid'],
    'muscle_pain':           ['nsaid', 'opioid', 'statin'],
    'muscle_wasting':        ['gluten', 'dairy'],
    'joint_pain':            ['dairy', 'gluten', 'nsaid'],
    'back_pain':             ['nsaid', 'dairy', 'gluten'],
    'neck_stiffness':        ['dairy', 'gluten', 'nsaid'],
    'painful_walking':       ['nsaid', 'dairy'],
    'palpitations':          ['dairy', 'gluten', 'sulfites', 'caffeine'],
    'fast_heart_rate':       ['nsaid', 'opioid', 'sulfites'],
    'shivering':             ['penicillin', 'sulfa'],
    'chills':                ['penicillin', 'sulfa', 'nsaid'],
    'high_fever':            ['penicillin', 'sulfa', 'nsaid'],
    'mild_fever':            ['penicillin', 'sulfa', 'nsaid'],
    'sweating':              ['opioid', 'nsaid'],
    'dehydration':           ['dairy', 'gluten'],
    'weight_loss':           ['gluten', 'dairy'],
    'weight_gain':           ['gluten', 'dairy'],

    # Urinary symptoms
    'burning_micturition':   ['sulfa', 'nsaid'],
    'spotting_urination':    ['sulfa', 'nsaid'],
    'bladder_discomfort':    ['sulfa', 'nsaid'],
    'continuous_feel_of_urine': ['sulfa', 'nsaid'],
    'foul_smell_of_urine':   ['sulfa', 'penicillin'],
    'dark_urine':            ['penicillin', 'sulfa', 'nsaid'],
    'yellow_urine':          ['penicillin', 'sulfa'],
    'polyuria':              ['dairy', 'gluten'],

    # Liver/blood symptoms
    'yellowish_skin':        ['penicillin', 'sulfa', 'nsaid'],
    'yellowing_of_eyes':     ['penicillin', 'sulfa', 'nsaid'],
    'acute_liver_failure':   ['nsaid', 'penicillin', 'sulfa'],
    'toxic_look':            ['penicillin', 'sulfa'],

    # Other
    'cold_hands_and_feets':  ['dairy', 'gluten'],
    'irregular_sugar_level': ['dairy', 'gluten'],
    'increased_appetite':    ['gluten', 'dairy'],
    'abnormal_menstruation': ['gluten', 'dairy'],
    'pain_during_bowel_movements': ['dairy', 'gluten', 'nsaid'],
    'pain_in_anal_region':   ['dairy', 'gluten'],
    'irritation_in_anus':    ['dairy', 'gluten'],
    'difficulty_in_swallowing': ['peanuts', 'shellfish', 'penicillin'],
    'loss_of_smell':         ['dairy', 'gluten'],
}

# Severity weight → BiteCheck severity label
def weight_to_severity(weight):
    if weight <= 2:   return 'mild'
    elif weight <= 4: return 'moderate'
    elif weight <= 6: return 'severe'
    else:             return 'critical'


def convert():
    print("=" * 60)
    print("  BiteCheck — Symptom Dataset Converter")
    print("=" * 60)

    # ── Load severity file ──────────────────────────────────
    if not SEVERITY_FILE.exists():
        print(f"ERROR: {SEVERITY_FILE} not found!")
        return

    severity_df = pd.read_csv(SEVERITY_FILE)
    print(f"\nLoaded {len(severity_df)} symptoms from severity file")

    # Build severity lookup
    severity_map = {}
    for _, row in severity_df.iterrows():
        symptom = str(row['Symptom']).strip().lower()
        weight  = int(row['weight'])
        severity_map[symptom] = {
            'weight':   weight,
            'severity': weight_to_severity(weight)
        }

    # ── Load description file ───────────────────────────────
    disease_descriptions = {}
    if DESCRIPTION_FILE.exists():
        desc_df = pd.read_csv(DESCRIPTION_FILE)
        for _, row in desc_df.iterrows():
            disease = str(row['Disease']).strip()
            desc    = str(row['Description']).strip()
            disease_descriptions[disease] = desc
        print(f"Loaded {len(disease_descriptions)} disease descriptions")

    # ── Build final SYMPTOM_ALLERGEN_HINTS ──────────────────
    print("\nBuilding symptom allergen hints...")

    symptom_hints = {}
    matched   = 0
    unmatched = 0

    for symptom, data in severity_map.items():
        allergens = SYMPTOM_ALLERGEN_MAP.get(symptom, [])

        # Also try clean name (replace _ with space)
        clean_symptom = symptom.replace('_', ' ')
        if not allergens:
            allergens = SYMPTOM_ALLERGEN_MAP.get(clean_symptom, [])

        if allergens:
            matched += 1
        else:
            unmatched += 1

        symptom_hints[clean_symptom] = {
            'allergens': allergens,
            'severity':  data['severity'],
            'weight':    data['weight'],
        }
        # Also store underscore version for lookup
        symptom_hints[symptom] = {
            'allergens': allergens,
            'severity':  data['severity'],
            'weight':    data['weight'],
        }

    print(f"  Symptoms with allergen hints: {matched}")
    print(f"  Symptoms without hints:       {unmatched}")
    print(f"  Total symptom entries:        {len(symptom_hints)}")

    # ── Save to JSON ────────────────────────────────────────
    output = {
        'symptom_hints':       symptom_hints,
        'disease_descriptions': disease_descriptions,
        'total_symptoms':      len(severity_map),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n✅ Saved → {OUTPUT_FILE}")

    # ── Preview ─────────────────────────────────────────────
    print("\nSample symptom hints:")
    samples = ['itching', 'breathlessness', 'stomach_pain',
               'headache', 'joint_pain', 'skin_rash']
    for s in samples:
        if s in symptom_hints:
            d = symptom_hints[s]
            print(f"  {s:<30} severity={d['severity']:<10} allergens={d['allergens']}")

    print("\n✅ Done! Now copy allergy/symptom_data.json to your project.")
    print("   The medicine_module.py will load it automatically.")
    print("\nRestart server: py manage.py runserver")


if __name__ == '__main__':
    convert()
