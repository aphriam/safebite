"""
BiteCheck — USDA Food Alternatives Builder
============================================
Builds food alternatives based on USDA nutritional equivalents.
No download needed — uses USDA official substitution guidelines.

Run: py build_food_alternatives.py
"""

import json
from pathlib import Path

OUTPUT = Path("allergy/usda_food_alternatives.json")

# ─── USDA BASED FOOD ALTERNATIVES ────────────────────────────
# Based on USDA MyPlate, FDA allergen guidance,
# and Academy of Nutrition and Dietetics substitution guides
alternatives = {

    # ── BIG 9 ALLERGENS ──────────────────────────────────────
    "peanuts": (
        "Sunflower seed butter, pumpkin seed butter, soy nut butter "
        "(if not soy allergic), sunflower seeds, pumpkin seeds, hemp seeds"
    ),
    "tree nuts": (
        "Sunflower seeds, pumpkin seeds, hemp seeds, roasted chickpeas, "
        "sunflower seed butter, tahini (if not sesame allergic)"
    ),
    "shellfish": (
        "White fish like cod or tilapia (if not fish allergic), "
        "chicken, turkey, tofu, jackfruit, mushrooms, hearts of palm"
    ),
    "fish": (
        "Chicken, turkey, tofu, tempeh, lentils, chickpeas, "
        "jackfruit (for texture), mushrooms, seitan (if not gluten allergic)"
    ),
    "dairy": (
        "Oat milk, coconut milk, almond milk (if not tree nut allergic), "
        "soy milk (if not soy allergic), rice milk, hemp milk, "
        "coconut yogurt, dairy-free cheese (check labels), nutritional yeast"
    ),
    "eggs": (
        "Flax egg (1 tbsp ground flax + 3 tbsp water), "
        "chia egg (1 tbsp chia + 3 tbsp water), aquafaba (chickpea water), "
        "applesauce (1/4 cup per egg), mashed banana, commercial egg replacers"
    ),
    "gluten": (
        "Rice flour, almond flour (if not tree nut allergic), "
        "coconut flour, cassava flour, tapioca starch, potato starch, "
        "corn flour (if not corn allergic), buckwheat, quinoa, millet, "
        "certified gluten-free oats, rice pasta, corn pasta, lentil pasta"
    ),
    "soy": (
        "Coconut aminos (soy sauce substitute), chickpeas, lentils, "
        "black beans, sunflower seeds, hemp seeds, pumpkin seeds, "
        "chicken or turkey (as protein substitute for tofu/tempeh)"
    ),
    "sesame": (
        "Pumpkin seed oil (for sesame oil), sunflower seed butter "
        "(for tahini), hemp seeds, flaxseeds, sunflower seeds"
    ),

    # ── EU ADDITIONAL ALLERGENS ───────────────────────────────
    "mustard": (
        "Horseradish, wasabi (check labels for mustard), "
        "celery seed, turmeric (for color), vinegar with herbs"
    ),
    "celery": (
        "Fennel, parsley, lovage, celeriac-free vegetable stocks, "
        "homemade stocks without celery"
    ),
    "lupin": (
        "Chickpea flour, rice flour, potato flour, "
        "tapioca starch as substitutes for lupin flour"
    ),
    "sulfites": (
        "Fresh unprocessed foods, organic wines without added sulfites, "
        "fresh fruit instead of dried, homemade condiments"
    ),

    # ── MEAT ALLERGENS ────────────────────────────────────────
    "beef": (
        "Turkey, chicken (if not chicken allergic), lamb, "
        "lentils, chickpeas, black beans, portobello mushrooms, "
        "jackfruit (for texture), tofu (if not soy allergic)"
    ),
    "pork": (
        "Turkey bacon, turkey sausage, chicken, beef (if not beef allergic), "
        "lamb, lentils, chickpeas, mushrooms for texture"
    ),
    "chicken": (
        "Turkey, fish (if not fish allergic), tofu, tempeh, "
        "lentils, chickpeas, jackfruit, seitan (if not gluten allergic)"
    ),
    "mutton": (
        "Beef (if not beef allergic), chicken, turkey, "
        "lentils, chickpeas, mushrooms"
    ),

    # ── FRUIT ALLERGENS ───────────────────────────────────────
    "kiwi": (
        "Strawberry, mango, papaya, pineapple — "
        "note: kiwi cross-reacts with latex and birch pollen"
    ),
    "strawberry": (
        "Blueberry, raspberry, blackberry, grape, "
        "watermelon, mango, papaya"
    ),
    "peach": (
        "Pear, grape, watermelon, cantaloupe — "
        "note: stone fruits often cross-react with each other"
    ),
    "banana": (
        "Mango, papaya, plantain — note: banana cross-reacts with latex"
    ),
    "avocado": (
        "Hummus (if not sesame allergic), olive tapenade, "
        "edamame spread (if not soy allergic) — "
        "note: avocado cross-reacts with latex"
    ),
    "tomato": (
        "Roasted red pepper, pumpkin puree, carrot-based sauces, "
        "beet for color in some dishes"
    ),

    # ── SPICE ALLERGENS ───────────────────────────────────────
    "garlic": (
        "Asafoetida (hing) in small amounts, chives, "
        "garlic-infused oil (low FODMAP), fennel seeds"
    ),
    "onion": (
        "Leek green tops only, chive flowers, "
        "spring onion green parts, fennel bulb"
    ),
    "cinnamon": (
        "Cardamom, nutmeg, allspice, mace, ginger "
        "as warming spice alternatives"
    ),

    # ── MEDICINE ALLERGENS ────────────────────────────────────
    "penicillin": (
        "Consult your doctor — possible alternatives include "
        "macrolides (azithromycin, erythromycin) or fluoroquinolones. "
        "Note: ~10% cross-reactivity with cephalosporins"
    ),
    "cephalosporin": (
        "Consult your doctor — possible alternatives include "
        "macrolides or fluoroquinolones depending on infection type"
    ),
    "sulfa": (
        "Consult your doctor — possible alternatives include "
        "trimethoprim alone, fluoroquinolones, or nitrofurantoin"
    ),
    "nsaid": (
        "Paracetamol/Acetaminophen for pain and fever "
        "(does not inhibit COX like NSAIDs). "
        "Consult doctor for anti-inflammatory alternatives"
    ),
    "opioid": (
        "Consult your doctor for non-opioid pain management: "
        "paracetamol, NSAIDs (if not NSAID allergic), "
        "nerve blocks, physical therapy, TENS"
    ),
    "quinolone": (
        "Consult your doctor — possible alternatives include "
        "macrolides, tetracyclines, or beta-lactams depending on infection"
    ),
    "macrolide": (
        "Consult your doctor — possible alternatives include "
        "doxycycline, fluoroquinolones, or beta-lactams"
    ),
    "tetracycline": (
        "Consult your doctor — possible alternatives include "
        "macrolides, fluoroquinolones, or beta-lactams"
    ),
    "statin": (
        "Consult your cardiologist — alternatives include "
        "ezetimibe, PCSK9 inhibitors, bile acid sequestrants, "
        "or a different statin (some are better tolerated)"
    ),
    "ace_inhibitor": (
        "Consult your doctor — ARBs (losartan, valsartan) "
        "are the main alternative; do not cause ACE-inhibitor cough"
    ),

    # ── OTHER ─────────────────────────────────────────────────
    "latex": (
        "Nitrile gloves, vinyl gloves, polyurethane gloves. "
        "Note: latex cross-reacts with banana, avocado, kiwi, chestnut"
    ),
    "oats": (
        "Rice, quinoa, buckwheat, millet, amaranth, "
        "certified gluten-free alternatives"
    ),
    "corn": (
        "Rice flour, potato starch, tapioca starch, arrowroot, "
        "cassava flour as thickening/binding alternatives"
    ),
    "gelatin": (
        "Agar agar (plant-based), pectin, carrageenan, "
        "guar gum, xanthan gum as gelling alternatives"
    ),
}

if __name__ == '__main__':
    print("=" * 55)
    print("  BiteCheck — Building USDA Food Alternatives")
    print("=" * 55)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(alternatives, f, indent=2)

    print(f"\n✅ Saved {len(alternatives)} allergen alternatives → {OUTPUT}")
    print("\nSample entries:")
    for allergen in ['peanuts', 'dairy', 'gluten', 'beef', 'nsaid']:
        print(f"  {allergen:<15} → {alternatives[allergen][:60]}...")

    print("\nRestart server: py manage.py runserver")
