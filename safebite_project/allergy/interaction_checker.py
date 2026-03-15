"""
BiteCheck — Drug Interaction Checker
======================================
Checks dangerous interactions between medicines.
"""

from .medicine_search import search_medicine


def check_drug_interactions(medicine_list):
    """
    Check interactions between multiple medicines.
    Returns list of dangerous interactions found.
    """
    if len(medicine_list) < 2:
        return {'error': 'Please provide at least 2 medicines'}

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

            db2      = search_medicine(med2)
            generic2 = str(db2.get('generic_name', med2)).lower() if db2 else med2.lower()

            if any(med2.lower() in inter or generic2 in inter
                   for inter in med1_interactions):
                interactions_found.append({
                    'medicine_1': med1,
                    'medicine_2': med2,
                    'severity':   'high',
                    'warning':    f'⚠️ {med1} may interact dangerously with {med2}',
                    'advice':     'Consult your doctor before taking these together'
                })

    return {
        'medicines_checked':  medicine_list,
        'total_interactions': len(interactions_found),
        'interactions':       interactions_found,
        'safe':               len(interactions_found) == 0,
        'recommendation': (
            '✅ No dangerous interactions found between these medicines.'
            if not interactions_found else
            f'🚨 {len(interactions_found)} dangerous interaction(s) found! Consult your doctor immediately.'
        )
    }
