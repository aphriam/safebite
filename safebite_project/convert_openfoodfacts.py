"""
BiteCheck — Open Food Facts Converter
=======================================

Converts the raw Open Food Facts CSV into BiteCheck's clean format:
    item_name | item_type | ingredients

HOW TO USE:
    1. Update INPUT_FILE path below to your downloaded file
    2. Run: py convert_openfoodfacts.py
"""

import pandas as pd
import re
from pathlib import Path

# ─── CONFIGURE THIS PATH ─────────────────────────────────────
INPUT_FILE  = Path(r"C:\Users\DELL\Desktop\openfoodfacts_export (1).csv")
OUTPUT_FILE = Path("openfoodfacts_converted.csv")
MERGE_INTO  = Path("dataset.csv")
MAX_ROWS    = 5000  # increase to None to process all rows

# ─── CATEGORY → ITEM TYPE ────────────────────────────────────
def get_item_type(categories):
    if pd.isna(categories) or not str(categories).strip():
        return 'food'
    cats = str(categories).lower()
    if any(w in cats for w in ['beverage','drink','juice','water','tea','coffee','soda','smoothie','lassi']):
        return 'drink'
    if any(w in cats for w in ['snack','chip','crisp','biscuit','cookie','cracker','popcorn','namkeen']):
        return 'snack'
    if any(w in cats for w in ['sweet','chocolate','candy','dessert','ice cream','mithai','halwa']):
        return 'sweet'
    if any(w in cats for w in ['sauce','condiment','ketchup','chutney','pickle','achar']):
        return 'condiment'
    if any(w in cats for w in ['breakfast','cereal','oat','muesli']):
        return 'breakfast'
    return 'food'

# ─── CLEAN INGREDIENTS ───────────────────────────────────────
def clean_ingredients(text):
    if pd.isna(text) or not str(text).strip():
        return None
    text = str(text).lower()
    text = re.sub(r'\(\s*\d+[\.,]?\d*\s*%\s*\)', '', text)
    text = re.sub(r'ingredients\s*:', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip('.,;: ')
    if len(text) < 10 or not re.search(r'[a-zA-Z]', text):
        return None
    return text

# ─── CLEAN NAME ──────────────────────────────────────────────
def clean_name(name, brand):
    if pd.isna(name) or not str(name).strip():
        return None
    name = str(name).strip()
    if not pd.isna(brand) and str(brand).strip():
        brand_str = str(brand).split(',')[0].strip()
        if brand_str.lower() not in name.lower() and len(brand_str) < 30:
            name = f"{brand_str} {name}"
    name = re.sub(r'[^\w\s\-\(\)\.]', '', name).strip()
    return name if len(name) >= 2 else None

# ─── AUTO DETECT SEPARATOR ───────────────────────────────────
def detect_separator(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        first_line = f.readline()
    tabs   = first_line.count('\t')
    commas = first_line.count(',')
    print(f"  Tabs in first line: {tabs}")
    print(f"  Commas in first line: {commas}")
    sep = '\t' if tabs > commas else ','
    print(f"  Using separator: {'TAB' if sep == chr(9) else 'COMMA'}")
    return sep

# ─── FIND CORRECT COLUMN NAMES ───────────────────────────────
def find_columns(df):
    """
    Open Food Facts has many language variants of columns.
    Find whichever ones are present.
    """
    cols = df.columns.tolist()
    print(f"\n  All columns found ({len(cols)} total):")
    print(f"  {cols[:20]}...")  # show first 20

    # Find product name column
    name_col = None
    for candidate in ['product_name', 'product_name_en', 'product_name_fr',
                       'product_name_de', 'name', 'product']:
        if candidate in cols:
            name_col = candidate
            break

    # Find ingredients column
    ingr_col = None
    for candidate in ['ingredients_text', 'ingredients_text_en', 'ingredients_text_fr',
                       'ingredients_text_de', 'ingredients', 'ingredients_text_it']:
        if candidate in cols:
            ingr_col = candidate
            break

    # Find brands column
    brand_col = 'brands' if 'brands' in cols else None

    # Find categories column
    cat_col = 'categories' if 'categories' in cols else None

    print(f"\n  Mapped columns:")
    print(f"    product name  → {name_col}")
    print(f"    ingredients   → {ingr_col}")
    print(f"    brands        → {brand_col}")
    print(f"    categories    → {cat_col}")

    return name_col, ingr_col, brand_col, cat_col

# ─── MAIN ────────────────────────────────────────────────────
def convert(input_path, output_path, max_rows=None):
    print(f"Reading: {input_path}")

    if not input_path.exists():
        print(f"\nERROR: File not found at: {input_path}")
        return None

    # Auto detect separator
    print("\nDetecting file format...")
    sep = detect_separator(input_path)

    # Read file
    print(f"\nLoading up to {max_rows or 'all'} rows...")
    df = pd.read_csv(
        input_path,
        sep=sep,
        nrows=max_rows,
        low_memory=False,
        on_bad_lines='skip',
        encoding='utf-8',
        encoding_errors='ignore',
    )
    print(f"Loaded {len(df):,} rows")

    # Find correct column names
    name_col, ingr_col, brand_col, cat_col = find_columns(df)

    if not name_col:
        print("\nERROR: Could not find product name column!")
        print("Available columns:", df.columns.tolist())
        return None

    if not ingr_col:
        print("\nERROR: Could not find ingredients column!")
        print("Available columns:", df.columns.tolist())
        return None

    # Convert rows
    print(f"\nConverting...")
    results = []
    skipped_no_name = 0
    skipped_no_ingr = 0

    for _, row in df.iterrows():
        name = clean_name(
            row.get(name_col),
            row.get(brand_col) if brand_col else None
        )
        if not name:
            skipped_no_name += 1
            continue

        ingredients = clean_ingredients(row.get(ingr_col))
        if not ingredients:
            skipped_no_ingr += 1
            continue

        item_type = get_item_type(row.get(cat_col) if cat_col else None)

        results.append({
            'item_name':   name,
            'item_type':   item_type,
            'ingredients': ingredients,
        })

    print(f"\nResults:")
    print(f"  ✅ Converted:           {len(results):,}")
    print(f"  ❌ Skipped (no name):   {skipped_no_name:,}")
    print(f"  ❌ Skipped (no ingr):   {skipped_no_ingr:,}")

    if not results:
        print("\nNo results! Printing first 3 rows to diagnose:")
        print(df.head(3).to_string())
        return None

    result_df = pd.DataFrame(results)
    result_df = result_df.drop_duplicates(subset=['item_name']).reset_index(drop=True)
    print(f"  📦 Final unique items:  {len(result_df):,}")

    print(f"\nSample output:")
    print(result_df[['item_name','item_type','ingredients']].head(5).to_string())

    result_df.to_csv(output_path, index=False)
    print(f"\n✅ Saved → {output_path}")
    return result_df

# ─── MERGE ───────────────────────────────────────────────────
def merge_with_existing(new_df, existing_path):
    if not existing_path.exists():
        print(f"No existing dataset — saving as new.")
        new_df.to_csv(existing_path, index=False)
        return

    print(f"\nMerging with {existing_path}...")
    existing_df = pd.read_csv(existing_path)
    print(f"  Existing: {len(existing_df):,} items")
    print(f"  New:      {len(new_df):,} items")

    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=['item_name']).reset_index(drop=True)
    print(f"  ✅ Total after merge: {len(combined):,} items")

    combined.to_csv(existing_path, index=False)
    print(f"  Saved → {existing_path}")

# ─── RUN ─────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  BiteCheck — Open Food Facts Converter")
    print("=" * 60)

    converted = convert(INPUT_FILE, OUTPUT_FILE, MAX_ROWS)

    if converted is not None:
        merge_with_existing(converted, MERGE_INTO)
        print("\n✅ Done! Now retrain your model:")
        print("   py allergy/train_model.py")