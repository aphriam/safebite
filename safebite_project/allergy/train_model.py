"""
BiteCheck — Clean Personalised Trainer v4
==========================================
Run: py allergy/train_model.py
"""

import sys
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
import joblib

BASE_DIR   = Path(__file__).resolve().parent.parent
DATASET    = BASE_DIR / 'dataset.csv'
MODEL_PATH = BASE_DIR / 'allergy' / 'allergy_model.pkl'

ALLERGEN_KEYWORDS = {
    'peanuts':       ['peanut', 'groundnut', 'arachis oil'],
    'tree nuts':     ['almond', 'cashew', 'walnut', 'pistachio', 'hazelnut',
                      'macadamia', 'pecan', 'brazil nut', 'pine nut', 'chestnut',
                      'praline', 'marzipan', 'nougat'],
    'shellfish':     ['shrimp', 'prawn', 'crab', 'lobster', 'scallop', 'clam',
                      'oyster', 'mussel', 'squid', 'octopus', 'shellfish', 'crayfish'],
    'fish':          ['salmon', 'tuna', 'cod', 'sardine', 'anchovy', 'mackerel',
                      'herring', 'trout', 'halibut', 'tilapia', 'swordfish',
                      'fish sauce', 'fish stock', 'fish paste'],
    'dairy':         ['milk', 'cream', 'butter', 'cheese', 'yogurt', 'lactose',
                      'whey', 'paneer', 'ghee', 'casein', 'mozzarella', 'parmesan',
                      'cheddar', 'custard', 'bechamel', 'hollandaise', 'ice cream',
                      'skimmed milk', 'milk powder', 'milk solids'],
    'eggs':          ['egg', 'eggs', 'albumin', 'mayonnaise', 'mayo', 'meringue'],
    'gluten':        ['wheat', 'gluten', 'flour', 'bread', 'pasta', 'barley',
                      'rye', 'semolina', 'noodle', 'bun', 'dough', 'pastry',
                      'croissant', 'cracker', 'biscuit', 'spelt', 'couscous', 'seitan'],
    'soy':           ['soy', 'soya', 'tofu', 'tempeh', 'edamame', 'miso',
                      'soybean', 'tamari', 'teriyaki', 'lecithins [soya]'],
    'sesame':        ['sesame', 'tahini', 'til', 'gingelly'],
    'mustard':       ['mustard'],
    'latex':         ['latex', 'natural rubber'],
    'oats':          ['oat', 'oats', 'oatmeal', 'granola'],
    'corn':          ['corn', 'maize', 'cornstarch', 'cornflour', 'corn syrup'],
    'sulfites':      ['sulfite', 'sulphite', 'sulphur dioxide', 'so2'],
    'penicillin':    ['penicillin', 'amoxicillin', 'ampicillin', 'flucloxacillin',
                      'cloxacillin', 'benzylpenicillin'],
    'cephalosporin': ['cephalosporin', 'cefalexin', 'cefuroxime', 'ceftriaxone', 'cefixime'],
    'sulfa':         ['sulfamethoxazole', 'sulfadiazine', 'sulfonamide'],
    'nsaid':         ['ibuprofen', 'naproxen', 'diclofenac', 'aspirin', 'indomethacin',
                      'ketoprofen', 'piroxicam', 'meloxicam', 'celecoxib', 'mefenamic acid',
                      'acetylsalicylic acid'],
    'opioid':        ['morphine', 'codeine', 'tramadol', 'oxycodone', 'fentanyl', 'pethidine'],
    'quinolone':     ['ciprofloxacin', 'levofloxacin', 'norfloxacin', 'ofloxacin', 'moxifloxacin'],
}

ALTERNATIVES = {
    'peanuts':       'Sunflower seed butter, pumpkin seed butter',
    'tree nuts':     'Sunflower seeds, pumpkin seeds, hemp seeds',
    'shellfish':     'White fish, chicken, tofu',
    'fish':          'Chicken, tofu, lentils, chickpeas',
    'dairy':         'Oat milk, coconut milk, almond milk, soy milk',
    'eggs':          'Flax egg, chia egg, aquafaba',
    'gluten':        'Rice flour, almond flour, corn tortilla, rice pasta',
    'soy':           'Coconut aminos, chickpeas, lentils',
    'sesame':        'Pumpkin seed oil, hemp seeds',
    'mustard':       'Horseradish, wasabi (check labels)',
    'penicillin':    'Consult doctor — alternatives: macrolides, cephalosporins',
    'nsaid':         'Paracetamol/Acetaminophen (consult doctor first)',
    'opioid':        'Consult doctor for non-opioid pain management',
}

if __name__ == '__main__':
    print("=" * 60)
    print("   BiteCheck — Clean Personalised Trainer v4")
    print("=" * 60)

    if not DATASET.exists():
        print(f"ERROR: dataset.csv not found at {DATASET}")
        sys.exit(1)

    df = pd.read_csv(DATASET)
    print(f"\nDataset: {len(df)} items")
    print(f"Columns: {df.columns.tolist()}")

    df['text'] = df['item_name'].str.lower() + ' ' + df['ingredients'].str.lower()

    print("\nBuilding ingredient vectorizer...")
    vectorizer = Pipeline([
        ('features', FeatureUnion([
            ('word', TfidfVectorizer(
                analyzer='word', ngram_range=(1, 3),
                max_features=10000, sublinear_tf=True
            )),
            ('char', TfidfVectorizer(
                analyzer='char_wb', ngram_range=(3, 5),
                max_features=6000, sublinear_tf=True
            )),
        ]))
    ])
    vectorizer.fit(df['text'])
    print("Vectorizer built.")

    # Save ONLY data — no functions saved
    model_data = {
        'vectorizer':        vectorizer,
        'allergen_keywords': ALLERGEN_KEYWORDS,
        'alternatives':      ALTERNATIVES,
    }
    joblib.dump(model_data, MODEL_PATH)
    print(f"Saved → {MODEL_PATH}")

    # Test allergen detection
    def detect(name, ingr):
        text = f"{name.lower()} {ingr.lower()}"
        return [a for a, kws in ALLERGEN_KEYWORDS.items() if any(k in text for k in kws)]

    print("\n--- Allergen Detection Tests ---")
    print(f"  {'Food / Medicine':<30} {'Allergens Detected'}")
    print("  " + "-" * 65)
    tests = [
        ("Peanut Butter",    "peanuts, salt, oil"),
        ("Grilled Chicken",  "chicken, olive oil, herbs, lemon"),
        ("Shrimp Pasta",     "shrimp, pasta, garlic, butter, cream"),
        ("Cheese Pizza",     "wheat flour, mozzarella, tomato, butter"),
        ("Mango Juice",      "mango, water, honey"),
        ("Pad Thai",         "rice noodles, shrimp, egg, fish sauce, peanuts"),
        ("Walnut Brownie",   "walnuts, chocolate, wheat flour, butter, eggs"),
        ("Idli",             "rice, urad dal, water, salt"),
        ("Amoxicillin",      "amoxicillin trihydrate, gelatin, magnesium stearate"),
        ("Ibuprofen",        "ibuprofen, microcrystalline cellulose, cornstarch"),
        ("Paracetamol",      "paracetamol, microcrystalline cellulose, starch"),
    ]
    for name, ingr in tests:
        found = detect(name, ingr)
        print(f"  {name:<30} {found if found else ['none']}")

    print("\n--- Personalised Risk Demo (User: peanuts + dairy) ---")
    user = ['peanuts', 'dairy']
    for name, ingr in tests:
        found   = detect(name, ingr)
        matched = [a for a in found if any(a in u or u in a for u in user)]
        if matched:    print(f"  HIGH 🚨  {name:<25} matched: {matched}")
        elif found:    print(f"  MEDIUM ⚠️  {name:<25} has: {found}")
        else:          print(f"  LOW ✅   {name:<25} no allergens")

    print("\nDone! Model saved.")
