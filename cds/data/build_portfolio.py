import json
import pandas as pd
from pathlib import Path
from cds.pricing.pd_table import rating_to_pd  # rating -> PD(T)

T = 5  # years
WEIGHT_COL = "Wgt"
RATING_COL = "RATING"

COARSE_MAP = {
    "AAA": "AAA",
    "AA+": "AA", "AA": "AA", "AA-": "AA",
    "A+": "A", "A": "A", "A-": "A",
    "BBB+": "BBB", "BBB": "BBB", "BBB-": "BBB",
    "BB+": "BB", "BB": "BB", "BB-": "BB",
    "B+": "B", "B": "B", "B-": "B",
    "CCC+": "CCC", "CCC": "CCC", "CCC-": "CCC",
    "CC": "CCC", "C": "CCC", "D": "CCC",
}

def coarse_rating(x):
    if x is None:
        return None
    x = str(x).strip()
    return COARSE_MAP.get(x)


def build_portfolio_df(path_json: str = "rating_data.json") -> pd.DataFrame:
    path = Path(__file__).parent / path_json
    with open(path, "r") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw["Data"])

    df[WEIGHT_COL] = pd.to_numeric(df[WEIGHT_COL], errors="coerce")
    df = df.dropna(subset=[WEIGHT_COL, RATING_COL]).copy()
    df["rating_coarse"] = df[RATING_COL].apply(coarse_rating)
    df = df.dropna(subset=["rating_coarse"])

    # Q_i(T) from rating table
    df["Q_T"] = df["rating_coarse"].apply(lambda r: rating_to_pd(r, T))
    df = df.dropna(subset=["Q_T"])

    df["w"] = df[WEIGHT_COL] / df[WEIGHT_COL].sum()

    return df[["rating_coarse", "Q_T", "w"]].reset_index(drop=True)