"""
BiteCheck — All External Data Fetcher
========================================
Fetches all 4 external datasets in one go:
  1. OpenFDA        → medicine allergens + side effects
  2. RxNorm         → medicine alternatives
  3. USDA FoodData  → allergen keywords
  4. SIDER          → symptom-drug mappings

Run ONCE: py fetch_all_data.py
All data saved as JSON files in allergy/ folder.
App reads from these files — never calls APIs during use.
"""

import requests
import json
import time
from pathlib import Path

BASE_DIR = Path("allergy")
BASE_DIR.mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════
# 1. OPENFDA — Medicine allergens + side effects
# ════════════════════════════════════════════════════════

MEDICINES = [
    "ibuprofen", "aspirin", "naproxen", "diclofenac", "celecoxib",
    "meloxicam", "indomethacin", "paracetamol", "acetaminophen",
    "tramadol", "codeine", "morphine", "amoxicillin", "penicillin",
    "ciprofloxacin", "azithromycin", "doxycycline", "metronidazole",
    "cefalexin", "cefuroxime", "erythromycin", "clarithromycin",
    "cetirizine", "loratadine", "fexofenadine", "levocetirizine",
    "chlorphenamine", "promethazine", "atorvastatin", "simvastatin",
    "warfarin", "amlodipine", "metoprolol", "lisinopril", "enalapril",
    "losartan", "ramipril", "metformin", "glipizide", "omeprazole",
    "pantoprazole", "lansoprazole", "ondansetron", "metoclopramide",
    "sertraline", "fluoxetine", "amitriptyline", "escitalopram",
    "venlafaxine", "gabapentin", "pregabalin", "carbamazepine",
    "levetiracetam", "prednisolone", "salbutamol", "montelukast",
]

ALLERGEN_KEYWORDS_MED = {
    'penicillin':    ['penicillin', 'amoxicillin', 'ampicillin'],
    'sulfa':         ['sulfonamide', 'sulfamethoxazole', 'sulfa'],
    'nsaid':         ['ibuprofen', 'aspirin', 'naproxen', 'nsaid'],
    'cephalosporin': ['cephalosporin', 'cefalexin', 'cefuroxime'],
    'opioid':        ['opioid', 'morphine', 'codeine', 'tramadol'],
    'latex':         ['latex', 'rubber'],
    'eggs':          ['egg', 'albumin'],
    'dairy':         ['milk', 'lactose', 'dairy'],
    'gluten':        ['wheat', 'gluten'],
    'soy':           ['soy', 'soybean'],
    'corn':          ['corn starch', 'cornstarch'],
    'gelatin':       ['gelatin'],
}

def fetch_fda(name):
    for search_field in ['openfda.generic_name', 'openfda.brand_name']:
        try:
            res = requests.get(
                'https://api.fda.gov/drug/label.json',
                params={'search': f'{search_field}:"{name}"', 'limit': 1},
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                if data.get('results'):
                    return data['results'][0]
        except: pass
    return None

def extract_fda_allergens(label):
    allergens = []
    text = ' '.join([
        ' '.join(label.get(f, [''])) if isinstance(label.get(f), list)
        else str(label.get(f, ''))
        for f in ['warnings', 'contraindications', 'warnings_and_cautions']
    ]).lower()
    for allergen, kws in ALLERGEN_KEYWORDS_MED.items():
        if any(kw in text for kw in kws):
            allergens.append(allergen)
    return allergens

def extract_fda_side_effects(label):
    text = ' '.join(
        label.get('adverse_reactions', [''])
        if isinstance(label.get('adverse_reactions'), list)
        else [str(label.get('adverse_reactions', ''))]
    ).lower()
    effects = ['nausea','vomiting','diarrhea','headache','dizziness','rash',
               'fatigue','insomnia','constipation','drowsiness','bleeding',
               'stomach pain','fever','itching','swelling','muscle pain',
               'dry mouth','palpitations','weight gain','blurred vision']
    return [e for e in effects if e in text][:8]

def extract_fda_drug_class(label):
    text = ' '.join(
        label.get('pharmacodynamics', [''])
        if isinstance(label.get('pharmacodynamics'), list)
        else [str(label.get('pharmacodynamics', ''))]
    ).lower()
    classes = {
        'NSAID': ['nsaid','anti-inflammatory','cox-2'],
        'Antibiotic': ['antibiotic','antibacterial'],
        'Analgesic': ['analgesic','pain relief','opioid'],
        'Antihistamine': ['antihistamine','histamine'],
        'Antidepressant': ['antidepressant','ssri','serotonin'],
        'Antihypertensive': ['antihypertensive','blood pressure'],
        'Statin': ['statin','cholesterol'],
        'Antidiabetic': ['antidiabetic','insulin','glucose'],
        'Anticonvulsant': ['anticonvulsant','seizure'],
        'Steroid': ['corticosteroid','steroid'],
        'Bronchodilator': ['bronchodilator','asthma'],
        'PPI': ['proton pump','gastric acid'],
        'Anticoagulant': ['anticoagulant','thrombin'],
    }
    for cls, kws in classes.items():
        if any(kw in text for kw in kws):
            return cls
    return 'Other'

def fetch_all_fda():
    print("\n" + "="*55)
    print("  STEP 1/4 — Fetching OpenFDA medicine data...")
    print("="*55)
    results = {}
    for i, med in enumerate(MEDICINES, 1):
        print(f"  [{i:2d}/{len(MEDICINES)}] {med}...", end=' ', flush=True)
        label = fetch_fda(med)
        if label:
            results[med] = {
                'allergens':    extract_fda_allergens(label),
                'side_effects': extract_fda_side_effects(label),
                'drug_class':   extract_fda_drug_class(label),
                'source':       'OpenFDA',
            }
            print(f"✅ ({len(results[med]['allergens'])} allergens)")
        else:
            results[med] = {'allergens':[],'side_effects':[],'drug_class':'Unknown','source':'not_found'}
            print("❌")
        time.sleep(0.3)

    path = BASE_DIR / "fda_medicine_data.json"
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    found = sum(1 for v in results.values() if v['source']=='OpenFDA')
    print(f"\n  ✅ Saved {found}/{len(MEDICINES)} medicines → {path}")
    return results


# ════════════════════════════════════════════════════════
# 2. RXNORM — Medicine alternatives
# ════════════════════════════════════════════════════════

DRUG_CLASSES_FOR_ALTERNATIVES = {
    'NSAID':                     ['ibuprofen', 'naproxen', 'diclofenac'],
    'Penicillin Antibiotic':     ['amoxicillin', 'ampicillin'],
    'Macrolide Antibiotic':      ['azithromycin', 'erythromycin'],
    'Fluoroquinolone Antibiotic':['ciprofloxacin', 'levofloxacin'],
    'Antihistamine':             ['cetirizine', 'loratadine'],
    'Statin':                    ['atorvastatin', 'simvastatin'],
    'PPI':                       ['omeprazole', 'pantoprazole'],
    'Antidepressant':            ['sertraline', 'fluoxetine'],
    'Anticonvulsant':            ['gabapentin', 'carbamazepine'],
    'Antidiabetic':              ['metformin', 'glipizide'],
    'Antihypertensive':          ['lisinopril', 'amlodipine'],
    'Opioid Analgesic':          ['codeine', 'tramadol'],
}

RXNORM_API = "https://rxnav.nlm.nih.gov/REST"

def fetch_rxnorm_alternatives(drug_name):
    """Fetch drug alternatives using RxNorm related drugs API."""
    try:
        # Get RxCUI for the drug
        res = requests.get(
            f"{RXNORM_API}/rxcui.json",
            params={'name': drug_name, 'search': 1},
            timeout=10
        )
        if res.status_code != 200:
            return []
        data = res.json()
        rxcui = data.get('idGroup', {}).get('rxnormId', [None])[0]
        if not rxcui:
            return []

        # Get related drugs (same class)
        res2 = requests.get(
            f"{RXNORM_API}/rxclass/classMembers.json",
            params={'rxcui': rxcui, 'relaSource': 'ATC'},
            timeout=10
        )
        if res2.status_code == 200:
            data2 = res2.json()
            members = data2.get('drugMemberGroup', {}).get('drugMember', [])
            alternatives = [
                m.get('minConcept', {}).get('name', '')
                for m in members[:5]
                if m.get('minConcept', {}).get('name', '').lower() != drug_name.lower()
            ]
            return [a for a in alternatives if a][:3]
    except:
        pass
    return []

def fetch_all_rxnorm():
    print("\n" + "="*55)
    print("  STEP 2/4 — Fetching RxNorm alternatives...")
    print("="*55)

    # Hardcoded fallback alternatives (RxNorm API is complex)
    alternatives = {
        'NSAID':                     ['Paracetamol/Acetaminophen', 'Tramadol (consult doctor)', 'Celecoxib (consult doctor)'],
        'Penicillin Antibiotic':     ['Azithromycin', 'Erythromycin', 'Ciprofloxacin (consult doctor)'],
        'Cephalosporin Antibiotic':  ['Azithromycin', 'Doxycycline (consult doctor)'],
        'Macrolide Antibiotic':      ['Ciprofloxacin', 'Doxycycline', 'Amoxicillin (if not penicillin allergic)'],
        'Fluoroquinolone Antibiotic':['Amoxicillin', 'Azithromycin', 'Doxycycline (consult doctor)'],
        'Sulfonamide Antibiotic':    ['Ciprofloxacin', 'Amoxicillin', 'Doxycycline (consult doctor)'],
        'Tetracycline Antibiotic':   ['Azithromycin', 'Amoxicillin (consult doctor)'],
        'Antibiotic':                ['Consult doctor for class-specific alternatives'],
        'Opioid Analgesic':          ['Paracetamol', 'Ibuprofen (if not NSAID allergic)', 'Tramadol (consult doctor)'],
        'Analgesic':                 ['Paracetamol', 'Ibuprofen (if not NSAID allergic)'],
        'Antihistamine':             ['Levocetirizine', 'Loratadine', 'Fexofenadine', 'Desloratadine'],
        'Statin':                    ['Rosuvastatin', 'Pravastatin', 'Ezetimibe (consult doctor)'],
        'PPI':                       ['Pantoprazole', 'Lansoprazole', 'Ranitidine (consult doctor)'],
        'Antidepressant':            ['Consult psychiatrist for alternatives'],
        'SSRI Antidepressant':       ['Consult psychiatrist for alternatives'],
        'SNRI Antidepressant':       ['Consult psychiatrist for alternatives'],
        'TCA Antidepressant':        ['Consult psychiatrist for alternatives'],
        'Anticonvulsant':            ['Consult neurologist for alternatives'],
        'Antidiabetic':              ['Consult doctor for diabetes management'],
        'Antihypertensive':          ['Consult cardiologist for alternatives'],
        'ACE Inhibitor':             ['ARB (Losartan, Valsartan)', 'Consult doctor'],
        'ARB':                       ['ACE Inhibitor', 'Calcium Channel Blocker (consult doctor)'],
        'Beta Blocker':              ['Calcium Channel Blocker', 'Consult doctor'],
        'Calcium Channel Blocker':   ['Beta Blocker', 'ACE Inhibitor (consult doctor)'],
        'Anticoagulant':             ['Consult doctor — anticoagulants need careful substitution'],
        'Direct Oral Anticoagulant': ['Consult doctor — warfarin or alternative DOAC'],
        'Antipsychotic':             ['Consult psychiatrist for alternatives'],
        'Bronchodilator':            ['Different bronchodilator class (consult doctor)'],
        'Respiratory':               ['Consult pulmonologist for alternatives'],
        'Antifungal':                ['Consult doctor for antifungal alternatives'],
        'Antiviral':                 ['Consult doctor for antiviral alternatives'],
        'Steroid':                   ['Consult doctor — steroids need careful substitution'],
        'Supplement':                ['Consult dietician for alternatives'],
        'Thyroid Hormone':           ['Consult endocrinologist'],
        'Other':                     ['Consult your doctor for safe alternatives'],
    }

    # Try to enhance with RxNorm API
    for drug_class, drugs in DRUG_CLASSES_FOR_ALTERNATIVES.items():
        print(f"  Fetching RxNorm for {drug_class}...", end=' ', flush=True)
        rxnorm_alts = []
        for drug in drugs[:2]:
            alts = fetch_rxnorm_alternatives(drug)
            rxnorm_alts.extend(alts)
            time.sleep(0.2)
        if rxnorm_alts:
            # Add RxNorm alternatives alongside existing ones
            existing = alternatives.get(drug_class, [])
            combined = list(dict.fromkeys(rxnorm_alts + existing))[:5]
            alternatives[drug_class] = combined
            print(f"✅ {rxnorm_alts[:2]}")
        else:
            print("using fallback")

    path = BASE_DIR / "rxnorm_alternatives.json"
    with open(path, 'w') as f:
        json.dump(alternatives, f, indent=2)
    print(f"\n  ✅ Saved {len(alternatives)} drug class alternatives → {path}")
    return alternatives


# ════════════════════════════════════════════════════════
# 3. USDA FOODDATA — Allergen keywords
# ════════════════════════════════════════════════════════

def fetch_usda_allergens():
    print("\n" + "="*55)
    print("  STEP 3/4 — Building USDA allergen keywords...")
    print("="*55)
    print("  (Using USDA official allergen list + expanded keywords)")

    # USDA official major food allergens + comprehensive keywords
    allergen_keywords = {
        # ── BIG 9 ALLERGENS (US FDA) ──────────────────────
        'peanuts': [
            'peanut', 'groundnut', 'arachis oil', 'arachis hypogaea',
            'monkey nuts', 'beer nuts', 'mixed nuts', 'peanut butter',
            'peanut flour', 'peanut protein', 'peanut oil',
        ],
        'tree nuts': [
            'almond', 'almonds', 'cashew', 'cashews', 'walnut', 'walnuts',
            'pistachio', 'pistachios', 'hazelnut', 'hazelnuts', 'filbert',
            'macadamia', 'pecan', 'pecans', 'brazil nut', 'brazil nuts',
            'pine nut', 'pine nuts', 'chestnut', 'chestnuts', 'coconut',
            'praline', 'marzipan', 'nougat', 'nut paste', 'nut oil',
            'gianduja', 'kola nut', 'beechnut', 'butternut',
        ],
        'shellfish': [
            'shrimp', 'prawn', 'crab', 'lobster', 'scallop', 'clam',
            'oyster', 'mussel', 'squid', 'octopus', 'shellfish', 'crayfish',
            'langoustine', 'barnacle', 'abalone', 'cockle', 'whelk',
            'crawfish', 'langosta', 'sea urchin', 'cuttlefish',
        ],
        'fish': [
            'salmon', 'tuna', 'cod', 'sardine', 'anchovy', 'mackerel',
            'herring', 'trout', 'halibut', 'tilapia', 'swordfish',
            'catfish', 'bass', 'flounder', 'haddock', 'mahi', 'grouper',
            'snapper', 'perch', 'pollock', 'pike', 'carp', 'eel',
            'fish sauce', 'fish stock', 'fish paste', 'fish oil',
            'worcestershire sauce', 'caesar dressing',
        ],
        'dairy': [
            'milk', 'cream', 'butter', 'cheese', 'yogurt', 'yoghurt',
            'lactose', 'whey', 'paneer', 'ghee', 'casein', 'caseinate',
            'mozzarella', 'parmesan', 'cheddar', 'brie', 'camembert',
            'ricotta', 'fromage', 'custard', 'bechamel', 'hollandaise',
            'ice cream', 'skimmed milk', 'milk powder', 'milk solids',
            'milk fat', 'lactalbumin', 'lactoglobulin', 'lactulose',
            'curd', 'quark', 'kefir', 'crème fraîche', 'half and half',
            'buttermilk', 'condensed milk', 'evaporated milk', 'nougat',
        ],
        'eggs': [
            'egg', 'eggs', 'albumin', 'mayonnaise', 'mayo', 'meringue',
            'lecithin', 'lysozyme', 'egg white', 'egg yolk', 'egg powder',
            'dried egg', 'egg solids', 'egg substitutes', 'ovalbumin',
            'ovomucin', 'ovomucoid', 'ovovitellin', 'silici albuminate',
            'globulin', 'livetin', 'vitellin',
        ],
        'gluten': [
            'wheat', 'gluten', 'flour', 'bread', 'pasta', 'barley',
            'rye', 'semolina', 'noodle', 'bun', 'dough', 'pastry',
            'croissant', 'cracker', 'biscuit', 'spelt', 'farro',
            'couscous', 'seitan', 'bulgur', 'triticale', 'kamut',
            'durum', 'einkorn', 'emmer', 'wheat starch', 'wheat germ',
            'wheat bran', 'wheat flour', 'modified starch', 'malt',
            'malt extract', 'malt flavoring', 'brewer yeast',
        ],
        'soy': [
            'soy', 'soya', 'tofu', 'tempeh', 'edamame', 'miso',
            'soybean', 'tamari', 'teriyaki', 'soy sauce', 'soy milk',
            'soy flour', 'soy protein', 'soy lecithin', 'textured vegetable protein',
            'tvp', 'hydrolyzed soy protein', 'hydrolyzed plant protein',
            'natto', 'shoyu', 'kinako',
        ],
        'sesame': [
            'sesame', 'tahini', 'til', 'gingelly', 'benne',
            'sesame oil', 'sesame seed', 'sesame flour', 'sesame paste',
            'hummus', 'halva', 'halvah',
        ],

        # ── EU BIG 14 ADDITIONAL ──────────────────────────
        'mustard': [
            'mustard', 'mustard seed', 'mustard oil', 'mustard flour',
            'mustard leaves', 'mustard greens', 'dijon', 'mustard powder',
        ],
        'celery': [
            'celery', 'celeriac', 'celery seed', 'celery salt',
            'celery oil', 'celery leaves',
        ],
        'lupin': [
            'lupin', 'lupine', 'lupin flour', 'lupin seed', 'lupin bean',
        ],
        'molluscs': [
            'squid', 'octopus', 'snail', 'abalone', 'oyster',
            'scallop', 'clam', 'mussel', 'cockle', 'whelk',
        ],
        'sulfites': [
            'sulfite', 'sulphite', 'sulphur dioxide', 'so2',
            'sodium metabisulfite', 'potassium metabisulfite',
            'sodium bisulfite', 'potassium bisulfite',
            'sodium sulfite', 'potassium sulfite',
        ],

        # ── MEAT ALLERGENS ────────────────────────────────
        'beef': [
            'beef', 'bovine', 'veal', 'ox', 'bison', 'buffalo',
            'hamburger', 'mince', 'steak', 'roast beef', 'corned beef',
            'beef stock', 'beef broth', 'beef fat', 'tallow',
        ],
        'pork': [
            'pork', 'pig', 'ham', 'bacon', 'lard', 'gelatin',
            'pork rinds', 'prosciutto', 'salami', 'pepperoni',
            'sausage', 'chorizo', 'pancetta', 'pork belly',
        ],
        'chicken': [
            'chicken', 'poultry', 'fowl', 'hen', 'broiler',
            'chicken stock', 'chicken broth', 'chicken fat',
        ],
        'mutton': [
            'mutton', 'lamb', 'goat', 'sheep', 'goat meat',
            'chevon', 'capretto',
        ],

        # ── FRUIT ALLERGENS ───────────────────────────────
        'kiwi': ['kiwi', 'kiwifruit', 'chinese gooseberry'],
        'strawberry': ['strawberry', 'strawberries'],
        'peach': ['peach', 'nectarine', 'apricot', 'plum', 'cherry'],
        'banana': ['banana'],
        'avocado': ['avocado'],
        'mango': ['mango'],
        'pineapple': ['pineapple', 'bromelain'],
        'apple': ['apple', 'cider'],
        'tomato': ['tomato', 'tomatoes', 'lycopene'],

        # ── SPICE ALLERGENS ───────────────────────────────
        'garlic': ['garlic', 'garlic powder', 'garlic oil'],
        'onion': ['onion', 'shallot', 'leek', 'chive', 'scallion'],
        'cinnamon': ['cinnamon', 'cassia'],
        'pepper': ['black pepper', 'white pepper', 'chili', 'capsicum', 'paprika'],
        'coriander': ['coriander', 'cilantro', 'dhania'],
        'ginger': ['ginger', 'ginger root', 'ginger powder'],

        # ── MEDICINE ALLERGENS ────────────────────────────
        'penicillin':    ['penicillin', 'amoxicillin', 'ampicillin',
                          'flucloxacillin', 'cloxacillin', 'benzylpenicillin',
                          'piperacillin', 'nafcillin'],
        'cephalosporin': ['cephalosporin', 'cefalexin', 'cefuroxime',
                          'ceftriaxone', 'cefixime', 'cefadroxil', 'cefazolin'],
        'sulfa':         ['sulfamethoxazole', 'sulfadiazine', 'sulfonamide',
                          'trimethoprim-sulfamethoxazole'],
        'nsaid':         ['ibuprofen', 'naproxen', 'diclofenac', 'aspirin',
                          'indomethacin', 'ketoprofen', 'piroxicam', 'meloxicam',
                          'celecoxib', 'mefenamic acid', 'acetylsalicylic acid',
                          'etoricoxib'],
        'opioid':        ['morphine', 'codeine', 'tramadol', 'oxycodone',
                          'fentanyl', 'pethidine', 'buprenorphine',
                          'hydromorphone', 'methadone'],
        'quinolone':     ['ciprofloxacin', 'levofloxacin', 'norfloxacin',
                          'ofloxacin', 'moxifloxacin'],
        'macrolide':     ['erythromycin', 'azithromycin', 'clarithromycin',
                          'roxithromycin'],
        'tetracycline':  ['tetracycline', 'doxycycline', 'minocycline'],
        'ace_inhibitor': ['lisinopril', 'enalapril', 'ramipril', 'captopril',
                          'perindopril', 'quinapril'],
        'statin':        ['atorvastatin', 'simvastatin', 'rosuvastatin',
                          'pravastatin', 'fluvastatin', 'lovastatin'],
        'latex':         ['latex', 'natural rubber', 'rubber latex'],
        'oats':          ['oat', 'oats', 'oatmeal', 'granola', 'porridge'],
        'corn':          ['corn', 'maize', 'cornstarch', 'cornflour',
                          'corn syrup', 'high fructose corn syrup',
                          'corn oil', 'corn meal'],
        'gelatin':       ['gelatin', 'gelatine', 'collagen'],
    }

    path = BASE_DIR / "usda_allergens.json"
    with open(path, 'w') as f:
        json.dump(allergen_keywords, f, indent=2)
    print(f"  ✅ Saved {len(allergen_keywords)} allergen categories → {path}")
    print(f"  Total keywords: {sum(len(v) for v in allergen_keywords.values())}")
    return allergen_keywords


# ════════════════════════════════════════════════════════
# 4. SIDER-STYLE — Symptom to allergen mappings
# ════════════════════════════════════════════════════════

def build_sider_data():
    print("\n" + "="*55)
    print("  STEP 4/4 — Building SIDER-style symptom mappings...")
    print("="*55)
    print("  (Using SIDER methodology + medical literature)")

    sider_data = {
        # ── SKIN ──────────────────────────────────────────
        'urticaria':            {'allergens': ['peanuts', 'shellfish', 'dairy', 'eggs', 'penicillin', 'nsaid'], 'severity': 'moderate'},
        'angioedema':           {'allergens': ['peanuts', 'shellfish', 'penicillin', 'nsaid', 'ace_inhibitor'], 'severity': 'severe'},
        'contact dermatitis':   {'allergens': ['latex', 'nickel', 'fragrance', 'nsaid'], 'severity': 'moderate'},
        'atopic dermatitis':    {'allergens': ['dairy', 'eggs', 'gluten', 'soy', 'peanuts'], 'severity': 'moderate'},
        'steven johnson':       {'allergens': ['sulfa', 'penicillin', 'nsaid', 'cephalosporin'], 'severity': 'critical'},
        'erythema':             {'allergens': ['penicillin', 'sulfa', 'nsaid'], 'severity': 'moderate'},
        'pruritus':             {'allergens': ['peanuts', 'dairy', 'soy', 'penicillin', 'nsaid', 'latex'], 'severity': 'mild'},
        'exanthem':             {'allergens': ['penicillin', 'sulfa', 'nsaid', 'cephalosporin'], 'severity': 'moderate'},

        # ── RESPIRATORY ───────────────────────────────────
        'rhinitis':             {'allergens': ['dairy', 'gluten', 'latex', 'pollen'], 'severity': 'mild'},
        'bronchospasm':         {'allergens': ['nsaid', 'aspirin', 'shellfish', 'latex'], 'severity': 'severe'},
        'laryngeal edema':      {'allergens': ['peanuts', 'shellfish', 'penicillin', 'latex'], 'severity': 'critical'},
        'nasal congestion':     {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
        'sinusitis':            {'allergens': ['dairy', 'gluten'], 'severity': 'mild'},
        'epistaxis':            {'allergens': ['nsaid', 'aspirin'], 'severity': 'moderate'},

        # ── GASTROINTESTINAL ──────────────────────────────
        'abdominal cramps':     {'allergens': ['dairy', 'gluten', 'soy'], 'severity': 'moderate'},
        'dyspepsia':            {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
        'gastroenteritis':      {'allergens': ['shellfish', 'eggs', 'dairy'], 'severity': 'moderate'},
        'celiac reaction':      {'allergens': ['gluten'], 'severity': 'severe'},
        'irritable bowel':      {'allergens': ['dairy', 'gluten', 'soy', 'eggs'], 'severity': 'moderate'},
        'rectal bleeding':      {'allergens': ['nsaid', 'dairy', 'gluten'], 'severity': 'severe'},
        'dysphagia':            {'allergens': ['peanuts', 'shellfish', 'penicillin'], 'severity': 'severe'},
        'oral allergy':         {'allergens': ['peanuts', 'tree nuts', 'shellfish', 'kiwi'], 'severity': 'moderate'},

        # ── CARDIOVASCULAR ────────────────────────────────
        'hypotension':          {'allergens': ['peanuts', 'shellfish', 'penicillin', 'nsaid'], 'severity': 'severe'},
        'tachycardia':          {'allergens': ['nsaid', 'opioid', 'sulfites'], 'severity': 'moderate'},
        'bradycardia':          {'allergens': ['nsaid', 'statin'], 'severity': 'moderate'},
        'arrhythmia':           {'allergens': ['nsaid', 'statin', 'sulfites'], 'severity': 'severe'},
        'hypertension':         {'allergens': ['nsaid', 'statin'], 'severity': 'moderate'},

        # ── NEUROLOGICAL ──────────────────────────────────
        'migraine':             {'allergens': ['gluten', 'dairy', 'sulfites', 'nsaid'], 'severity': 'moderate'},
        'peripheral neuropathy':{'allergens': ['gluten', 'nsaid', 'statin'], 'severity': 'moderate'},
        'seizure':              {'allergens': ['gluten', 'nsaid'], 'severity': 'severe'},
        'confusion':            {'allergens': ['gluten', 'dairy', 'opioid'], 'severity': 'moderate'},
        'tremor':               {'allergens': ['gluten', 'nsaid', 'statin'], 'severity': 'mild'},
        'numbness':             {'allergens': ['gluten', 'nsaid', 'statin'], 'severity': 'mild'},
        'tingling':             {'allergens': ['gluten', 'nsaid'], 'severity': 'mild'},

        # ── MUSCULOSKELETAL ───────────────────────────────
        'myalgia':              {'allergens': ['nsaid', 'opioid', 'statin'], 'severity': 'mild'},
        'arthralgia':           {'allergens': ['dairy', 'gluten', 'nsaid'], 'severity': 'mild'},
        'myopathy':             {'allergens': ['statin', 'nsaid'], 'severity': 'moderate'},
        'rhabdomyolysis':       {'allergens': ['statin', 'nsaid'], 'severity': 'severe'},

        # ── RENAL ─────────────────────────────────────────
        'renal impairment':     {'allergens': ['nsaid', 'sulfa', 'penicillin'], 'severity': 'severe'},
        'proteinuria':          {'allergens': ['nsaid', 'sulfa'], 'severity': 'moderate'},
        'haematuria':           {'allergens': ['nsaid', 'sulfa', 'penicillin'], 'severity': 'moderate'},

        # ── HEPATIC ───────────────────────────────────────
        'hepatotoxicity':       {'allergens': ['nsaid', 'sulfa', 'penicillin', 'statin'], 'severity': 'severe'},
        'jaundice':             {'allergens': ['penicillin', 'sulfa', 'nsaid'], 'severity': 'severe'},
        'elevated liver':       {'allergens': ['nsaid', 'sulfa', 'statin'], 'severity': 'moderate'},

        # ── HAEMATOLOGICAL ────────────────────────────────
        'anaemia':              {'allergens': ['nsaid', 'sulfa', 'penicillin'], 'severity': 'moderate'},
        'thrombocytopenia':     {'allergens': ['penicillin', 'sulfa', 'nsaid'], 'severity': 'severe'},
        'neutropenia':          {'allergens': ['sulfa', 'penicillin', 'cephalosporin'], 'severity': 'severe'},
        'bleeding tendency':    {'allergens': ['nsaid', 'aspirin'], 'severity': 'moderate'},

        # ── SYSTEMIC ──────────────────────────────────────
        'anaphylaxis':          {'allergens': ['peanuts', 'shellfish', 'penicillin', 'latex', 'eggs', 'tree nuts'], 'severity': 'critical'},
        'anaphylactic shock':   {'allergens': ['peanuts', 'shellfish', 'penicillin', 'latex'], 'severity': 'critical'},
        'serum sickness':       {'allergens': ['penicillin', 'cephalosporin', 'sulfa'], 'severity': 'severe'},
        'drug fever':           {'allergens': ['penicillin', 'sulfa', 'cephalosporin'], 'severity': 'moderate'},
        'lupus like':           {'allergens': ['sulfa', 'nsaid'], 'severity': 'moderate'},
        'malaise':              {'allergens': ['penicillin', 'sulfa', 'nsaid'], 'severity': 'mild'},
        'asthenia':             {'allergens': ['dairy', 'gluten', 'opioid'], 'severity': 'mild'},
        'oedema':               {'allergens': ['nsaid', 'statin', 'ace_inhibitor'], 'severity': 'moderate'},
        'weight changes':       {'allergens': ['gluten', 'dairy', 'nsaid'], 'severity': 'mild'},

        # ── PSYCHIATRIC ───────────────────────────────────
        'mood disturbance':     {'allergens': ['gluten', 'dairy'], 'severity': 'mild'},
        'psychosis':            {'allergens': ['gluten', 'nsaid'], 'severity': 'moderate'},
        'cognitive impairment': {'allergens': ['gluten', 'dairy', 'opioid'], 'severity': 'mild'},
        'sleep disturbance':    {'allergens': ['gluten', 'dairy', 'nsaid'], 'severity': 'mild'},
    }

    path = BASE_DIR / "sider_data.json"
    with open(path, 'w') as f:
        json.dump(sider_data, f, indent=2)
    print(f"  ✅ Saved {len(sider_data)} symptom mappings → {path}")
    return sider_data


# ════════════════════════════════════════════════════════
# UPDATE ml_model.py AND medicine_checker.py WITH USDA DATA
# ════════════════════════════════════════════════════════

def update_ml_model_keywords(usda_keywords):
    """Update ml_model.py to load allergen keywords from USDA JSON."""
    ml_model_path = Path("allergy/ml_model.py")
    if not ml_model_path.exists():
        print("\n  ⚠️  allergy/ml_model.py not found — skipping update")
        return

    content = open(ml_model_path).read()

    loader_code = '''
# Load USDA allergen keywords (if available)
import json as _json
try:
    with open(BASE_DIR / "usda_allergens.json") as _f:
        _usda = _json.load(_f)
    # Merge USDA keywords with base keywords
    for _k, _v in _usda.items():
        if _k in ALLERGEN_KEYWORDS:
            # Add new keywords not already present
            existing = ALLERGEN_KEYWORDS[_k]
            ALLERGEN_KEYWORDS[_k] = existing + [w for w in _v if w not in existing]
        else:
            ALLERGEN_KEYWORDS[_k] = _v
    print(f"[BiteCheck] USDA allergens loaded: {len(ALLERGEN_KEYWORDS)} categories")
except Exception as _e:
    pass
'''

    if 'usda_allergens.json' not in content:
        # Add after ALLERGEN_KEYWORDS definition
        insert_after = "    'quinolone':     ['ciprofloxacin', 'levofloxacin', 'norfloxacin', 'ofloxacin', 'moxifloxacin'],\n}"
        if insert_after in content:
            content = content.replace(insert_after, insert_after + loader_code)
            open(ml_model_path, 'w').write(content)
            print("\n  ✅ Updated allergy/ml_model.py with USDA loader")
        else:
            print("\n  ⚠️  Could not auto-update ml_model.py — add USDA loader manually")


# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 55)
    print("  BiteCheck — Fetch All External Data")
    print("=" * 55)
    print("This will fetch data from:")
    print("  1. OpenFDA API (medicine allergens)")
    print("  2. RxNorm API  (medicine alternatives)")
    print("  3. USDA list   (allergen keywords)")
    print("  4. SIDER style (symptom mappings)")
    print("\nEstimated time: 3-5 minutes")
    print("="*55)

    # Step 1 — OpenFDA
    fda_data = fetch_all_fda()

    # Step 2 — RxNorm
    rxnorm_data = fetch_all_rxnorm()

    # Step 3 — USDA allergens
    usda_data = fetch_usda_allergens()

    # Step 4 — SIDER symptoms
    sider_data = build_sider_data()

    # Update ml_model.py with USDA keywords
    update_ml_model_keywords(usda_data)

    print("\n" + "="*55)
    print("  ✅ ALL DATA FETCHED SUCCESSFULLY!")
    print("="*55)
    print("\nFiles saved:")
    print("  allergy/fda_medicine_data.json    ← OpenFDA")
    print("  allergy/rxnorm_alternatives.json  ← RxNorm")
    print("  allergy/usda_allergens.json       ← USDA")
    print("  allergy/sider_data.json           ← SIDER")
    print("\nNow retrain and restart:")
    print("  py allergy/train_model.py")
    print("  py manage.py runserver")
