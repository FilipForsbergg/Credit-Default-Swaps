import json
import pandas as pd
from pathlib import Path
from cds.pricing.pd_table import rating_to_pd  # rating -> PD(T)

T = 5  # years
WEIGHT_COL = "Wgt"
RATING_COL = "RATING"

PATH_RATING = "xover_s43.json"
PATH_MARKET_SPREADS = "spreads.json"


def load_json(path_json):
    path = Path(__file__).parent / path_json
    with open(path, "r") as f:
        return json.load(f)

def build_rating_df(path_json: str = PATH_RATING):
    raw = load_json(path_json)
    df = pd.DataFrame(raw["Data"])

    df[WEIGHT_COL] = pd.to_numeric(df[WEIGHT_COL], errors="coerce")
    
    is_missing = (
        df[RATING_COL].isna() |
        (df[RATING_COL].apply(lambda x: str(x).strip() == ""))
    )
    missing_data = df[is_missing]
    if not missing_data.empty:
        names = missing_data["Company Name"]
        print(f"Dropping companies with missing rating: {', '.join(map(str, names))}")

    df = df[~is_missing].copy()

    return df[["Company Name", RATING_COL]].reset_index(drop=True)

def build_portfolio_df(path_json: str = "rating_data.json") -> pd.DataFrame:
    raw = load_json(path_json)
    df = pd.DataFrame(raw["Data"])

    df[WEIGHT_COL] = pd.to_numeric(df[WEIGHT_COL], errors="coerce")
    df = df.dropna(subset=[WEIGHT_COL, RATING_COL]).copy()
    df["rating_coarse"] = df[RATING_COL]#.apply(coarse_rating)
    df = df.dropna(subset=["rating_coarse"])

    # Q_i(T) from rating table
    df["Q_T"] = df["rating_coarse"].apply(lambda r: rating_to_pd(r, T))
    df = df.dropna(subset=["Q_T"])

    df["w"] = df[WEIGHT_COL] / df[WEIGHT_COL].sum()

    return df[["rating_coarse", "Q_T", "w"]].reset_index(drop=True)

def spreads_to_df(path_json: str = PATH_MARKET_SPREADS) -> pd.DataFrame:
    raw = load_json(path_json)
    rows = []
    for c in raw:
        company = c["Company"]

        for entry in c["Data"]:
            rows.append({
                "Company": company,
                "Date": pd.to_datetime(entry["Date"]),
                "Spread": entry["Spread"],
            })

    df = pd.DataFrame(rows)
    df = df.sort_values(["Company", "Date"])
    return df

if __name__ == "__main__":
    df = spreads_to_df()
    print(df.head())