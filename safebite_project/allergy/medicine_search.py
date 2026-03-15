"""
BiteCheck — Medicine Search Module
====================================
Handles searching medicines from database.
"""

import pandas as pd
from pathlib import Path
from difflib import get_close_matches

BASE_DIR = Path(__file__).resolve().parent

# Load medicine database
try:
    medicine_db = pd.read_csv(BASE_DIR / "medicine_database.csv")
    print(f"[BiteCheck] Loaded {len(medicine_db)} medicines from database")
except:
    medicine_db = pd.DataFrame()
    print("[BiteCheck] WARNING: medicine_database.csv not found")


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
