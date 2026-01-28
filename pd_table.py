import re
from typing import Optional

"""
Average cumulative default probabilites for different credit-ratings and time horizons.
Source: Table 24.1 in Hull.
"""

PD_TABLE = {
"AAA": {"1": 0.0000, "2": 0.0003, "3": 0.0013, "4": 0.0024, "5": 0.0035, "7": 0.0051, "10": 0.0070, "15": 0.0091},
"AA": {"1": 0.0002, "2": 0.0006, "3": 0.0012, "4": 0.0021, "5": 0.0031, "7": 0.0050, "10": 0.0072, "15": 0.0102},
"A": {"1": 0.0005, "2": 0.0014, "3": 0.0023, "4": 0.0035, "5": 0.0047, "7": 0.0079, "10": 0.0124, "15": 0.0189},
"BBB": {"1": 0.0016, "2": 0.0045, "3": 0.0078, "4": 0.0117, "5": 0.0158, "7": 0.0233, "10": 0.0332, "15": 0.0469},
"BB": {"1": 0.0061, "2": 0.0192, "3": 0.0348, "4": 0.0505, "5": 0.0652, "7": 0.0901, "10": 0.1178, "15": 0.1467},
"B": {"1": 0.0333, "2": 0.0771, "3": 0.1155, "4": 0.1458, "5": 0.1693, "7": 0.2036, "10": 0.2374, "15": 0.2712},
"CCC": {"1": 0.2708, "2": 0.3664, "3": 0.4141, "4": 0.4410, "5": 0.4619, "7": 0.4826, "10": 0.5038, "15": 0.5259},
}

RATING_REGEX = re.compile(
r"(AAA|AA\+|AA|AA-|A\+|A|A-|BBB\+|BBB|BBB-|BB\+|BB|BB-|B\+|B|B-|CCC\+|CCC|CCC-|CC|C|D)"
)

def clean_rating(rating) -> Optional[str]:
    if rating is None:
        return None

    s = str(rating).strip().upper()
    if s in {"", "NAN", "NONE"}:
        return None

    m = RATING_REGEX.search(s) # <-- search istället för match
    return m.group(1) if m else None

def rating_to_pd(rating: str, horizon_years: int) -> float:
    horizon_years = str(horizon_years)
    rating = clean_rating(rating)

    # Translate data to match keys in PD_TABLE
    translate_ratings = {
        "AAA": "AAA",
        "AA+": "AA", "AA": "AA", "AA-": "AA",
        "A+": "A", "A": "A", "A-": "A",
        "BBB+": "BBB", "BBB": "BBB", "BBB-": "BBB",
        "BB+": "BB", "BB": "BB", "BB-": "BB",
        "B+": "B", "B": "B", "B-": "B",
        "CCC+": "CCC", "CCC": "CCC", "CCC-": "CCC",
        "CC": "CCC", "C": "CCC",
        "D": "CCC",
    }
    
    if rating not in translate_ratings:
        return None
    rating = translate_ratings[rating]
    if horizon_years not in PD_TABLE[rating]:
        return None
    
    default_prob = PD_TABLE[rating][horizon_years]
    return float(default_prob)