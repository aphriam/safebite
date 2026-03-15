"""
BiteCheck — DrugBank Converter
================================
Converts drugbank_clean.csv into BiteCheck's medicine_database.csv format:
    medicine_name | generic_name | drug_class | ingredients | interactions | side_effects

HOW TO USE:
    1. Place this script in your project folder
    2. Run: py convert_drugbank.py
"""

import pandas as pd
import re
from pathlib import Path

# ─── PATHS ───────────────────────────────────────────────────
INPUT_FILE  = Path(r"C:\Users\DELL\Desktop\drugbank_clean.csv")
OUTPUT_FILE = Path("drugbank_converted.csv")
MERGE_INTO  = Path("allergy/medicine_database.csv")
MAX_ROWS    = 2000  # increase to None for all rows

# ─── EXTRACT DRUG CLASS FROM ATC CODES / DESCRIPTION ─────────
def get_drug_class(atc, indication, description):
    text = f"{str(atc)} {str(indication)} {str(description)}".lower()

    if any(w in text for w in ['antibiotic', 'penicillin', 'amoxicillin', 'cephalosporin',
                                'macrolide', 'fluoroquinolone', 'tetracycline']):
        return 'Antibiotic'
    if any(w in text for w in ['antidepressant', 'ssri', 'snri', 'serotonin reuptake']):
        return 'Antidepressant'
    if any(w in text for w in ['antipsychotic', 'schizophrenia', 'dopamine antagonist']):
        return 'Antipsychotic'
    if any(w in text for w in ['anticonvulsant', 'antiepileptic', 'seizure']):
        return 'Anticonvulsant'
    if any(w in text for w in ['analgesic', 'pain relief', 'opioid', 'narcotic']):
        return 'Analgesic'
    if any(w in text for w in ['nsaid', 'anti-inflammatory', 'ibuprofen', 'naproxen']):
        return 'NSAID'
    if any(w in text for w in ['antihypertensive', 'blood pressure', 'beta blocker',
                                'ace inhibitor', 'calcium channel']):
        return 'Antihypertensive'
    if any(w in text for w in ['anticoagulant', 'antiplatelet', 'thrombin', 'warfarin']):
        return 'Anticoagulant'
    if any(w in text for w in ['antidiabetic', 'diabetes', 'insulin', 'glucose']):
        return 'Antidiabetic'
    if any(w in text for w in ['antihistamine', 'histamine', 'allergy']):
        return 'Antihistamine'
    if any(w in text for w in ['statin', 'cholesterol', 'lipid']):
        return 'Statin'
    if any(w in text for w in ['antifungal', 'fungal']):
        return 'Antifungal'
    if any(w in text for w in ['antiviral', 'virus', 'hiv', 'hepatitis']):
        return 'Antiviral'
    if any(w in text for w in ['diuretic', 'urine', 'renal']):
        return 'Diuretic'
    if any(w in text for w in ['bronchodilator', 'asthma', 'respiratory', 'inhaler']):
        return 'Respiratory'
    if any(w in text for w in ['proton pump', 'antacid', 'stomach', 'gastric']):
        return 'Gastrointestinal'
    if any(w in text for w in ['vitamin', 'supplement', 'mineral', 'deficiency']):
        return 'Supplement'
    if any(w in text for w in ['vaccine', 'immunization', 'immunoglobulin']):
        return 'Vaccine'
    if any(w in text for w in ['hormone', 'thyroid', 'estrogen', 'testosterone']):
        return 'Hormone'
    if any(w in text for w in ['chemotherapy', 'antineoplastic', 'cancer', 'tumor']):
        return 'Anticancer'
    return 'Other'


def clean_text(val, max_len=500):
    if pd.isna(val) or not str(val).strip():
        return ''
    text = str(val).strip()
    # Remove reference codes like [L41539]
    text = re.sub(r'\[[\w]+\]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len]


def extract_ingredients(description, mechanism):
    """Extract key chemical ingredients from description/mechanism."""
    text = clean_text(description) + ' ' + clean_text(mechanism)
    # Try to find excipient-like words
    common_excipients = ['microcrystalline cellulose', 'lactose', 'starch',
                         'magnesium stearate', 'gelatin', 'sucrose', 'water']
    found = [e for e in common_excipients if e in text.lower()]
    if found:
        return ', '.join(found)
    return 'active pharmaceutical ingredient'


def extract_interactions(drug_interactions):
    """Extract first few drug interaction names."""
    if pd.isna(drug_interactions) or not str(drug_interactions).strip():
        return ''
    text = str(drug_interactions)
    # Extract DB codes — these are drug IDs, get first 5
    db_codes = re.findall(r'DB\d{5}', text)
    if db_codes:
        return ', '.join(db_codes[:5]) + ' (see DrugBank for full list)'
    # Otherwise take first 200 chars
    return clean_text(drug_interactions, 200)


def extract_side_effects(toxicity, pharmacodynamics):
    """Extract side effects from toxicity and pharmacodynamics."""
    text = clean_text(toxicity, 300) + ' ' + clean_text(pharmacodynamics, 300)
    if not text.strip():
        return 'consult prescribing information'

    # Look for common side effect words
    side_effects = []
    keywords = ['nausea', 'vomiting', 'diarrhea', 'headache', 'dizziness',
                'rash', 'fatigue', 'bleeding', 'drowsiness', 'insomnia',
                'constipation', 'fever', 'pain', 'swelling', 'weakness',
                'hypotension', 'hypertension', 'tachycardia', 'bradycardia']
    for kw in keywords:
        if kw in text.lower():
            side_effects.append(kw)

    return ', '.join(side_effects[:6]) if side_effects else 'consult prescribing information'


# ─── MAIN ────────────────────────────────────────────────────
def convert(input_path, output_path, max_rows=None):
    print(f"Reading: {input_path}")

    if not input_path.exists():
        print(f"ERROR: File not found at {input_path}")
        return None

    print(f"Loading up to {max_rows or 'all'} rows...")
    df = pd.read_csv(
        input_path,
        nrows=max_rows,
        low_memory=False,
        on_bad_lines='skip',
        encoding='utf-8',
        encoding_errors='ignore',
    )
    print(f"Loaded {len(df):,} rows")
    print(f"Columns: {df.columns.tolist()[:10]}...")

    results = []
    skipped = 0

    for _, row in df.iterrows():
        # Get medicine name
        name = str(row.get('name', '')).strip()
        if not name or name == 'nan' or len(name) < 2:
            skipped += 1
            continue

        # Skip if not approved drug
        groups = str(row.get('groups', '')).lower()
        if 'approved' not in groups and 'investigational' not in groups:
            skipped += 1
            continue

        # Get generic name (same as name for DrugBank)
        generic_name = name

        # Get drug class
        drug_class = get_drug_class(
            row.get('atc-codes', ''),
            row.get('indication', ''),
            row.get('description', '')
        )

        # Get ingredients
        ingredients = extract_ingredients(
            row.get('description', ''),
            row.get('mechanism-of-action', '')
        )

        # Get interactions
        interactions = extract_interactions(row.get('drug-interactions', ''))

        # Get side effects
        side_effects = extract_side_effects(
            row.get('toxicity', ''),
            row.get('pharmacodynamics', '')
        )

        results.append({
            'medicine_name': name,
            'generic_name':  generic_name,
            'drug_class':    drug_class,
            'ingredients':   ingredients,
            'interactions':  interactions,
            'side_effects':  side_effects,
        })

    print(f"\nResults:")
    print(f"  ✅ Converted:  {len(results):,}")
    print(f"  ❌ Skipped:    {skipped:,}")

    if not results:
        print("No results! Check the file.")
        return None

    result_df = pd.DataFrame(results)
    result_df = result_df.drop_duplicates(subset=['medicine_name']).reset_index(drop=True)
    print(f"  📦 Unique:     {len(result_df):,}")

    print(f"\nSample:")
    print(result_df[['medicine_name', 'drug_class', 'side_effects']].head(8).to_string())

    result_df.to_csv(output_path, index=False)
    print(f"\n✅ Saved → {output_path}")
    return result_df


def merge_with_existing(new_df, existing_path):
    if not existing_path.exists():
        print(f"No existing file — saving as new.")
        new_df.to_csv(existing_path, index=False)
        return

    print(f"\nMerging with {existing_path}...")
    existing_df = pd.read_csv(existing_path)

    # Make sure columns match
    for col in ['medicine_name', 'generic_name', 'drug_class',
                 'ingredients', 'interactions', 'side_effects']:
        if col not in existing_df.columns:
            existing_df[col] = ''

    existing_df = existing_df[['medicine_name', 'generic_name', 'drug_class',
                                'ingredients', 'interactions', 'side_effects']]

    print(f"  Existing: {len(existing_df):,}")
    print(f"  New:      {len(new_df):,}")

    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=['medicine_name']).reset_index(drop=True)
    print(f"  ✅ Total after merge: {len(combined):,}")

    combined.to_csv(existing_path, index=False)
    print(f"  Saved → {existing_path}")


if __name__ == '__main__':
    print("=" * 60)
    print("  BiteCheck — DrugBank Converter")
    print("=" * 60)

    converted = convert(INPUT_FILE, OUTPUT_FILE, MAX_ROWS)

    if converted is not None:
        merge_with_existing(converted, MERGE_INTO)
        print("\n✅ Done! Restart your server:")
        print("   py manage.py runserver")
