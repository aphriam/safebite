"""
BiteCheck — Medicine Module (Main Entry Point)
================================================
This file just imports from the split modules.
Kept for backward compatibility with views.py.

Split modules:
  - medicine_search.py     → search_medicine()
  - medicine_checker.py    → check_medicine_allergens()
  - interaction_checker.py → check_drug_interactions()
  - symptom_analyser.py    → analyze_symptoms()
"""

from .medicine_search import search_medicine
from .medicine_checker import check_medicine_allergens
from .interaction_checker import check_drug_interactions
from .symptom_analyser import analyze_symptoms

__all__ = [
    'search_medicine',
    'check_medicine_allergens',
    'check_drug_interactions',
    'analyze_symptoms',
]
