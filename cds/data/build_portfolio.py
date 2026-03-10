import json
import pandas as pd
from pathlib import Path
from cds.pricing.pd_table import rating_to_pd  # rating -> PD(T)

T = 5  # years
WEIGHT_COL = "Wgt"
RATING_COL = "RATING"

PATH_RATING = "xover_s43.json"
PATH_MARKET_SPREADS = "spreads.json"
PATH_MARKET_INDEX_EXCEL = "timeserieItems.xlsx"

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
        # Set rating to BBB if missing
        df.loc[is_missing, RATING_COL] = "BBB"

        names = missing_data["Company Name"]
        print(f"Companies with missing rating: {', '.join(map(str, names))}")

    df = df[~is_missing].copy()

    return df[["Company Name", RATING_COL]].reset_index(drop=True)

def build_portfolio_df(path_rating = PATH_RATING, path_spreads = PATH_MARKET_SPREADS) -> pd.DataFrame:
    rating_df = build_rating_df(path_rating)
    market_spreads_df = spreads_to_df(path_spreads)
    return pd.merge(rating_df, market_spreads_df, left_on="Company Name", right_on="Company", how="inner")

def spreads_to_df(path_json: str = PATH_MARKET_SPREADS) -> pd.DataFrame:
    raw = load_json(path_json)
    rows = []
    for c in raw:
        company = c["Company"]

        for entry in c["Data"]:
            rows.append({
                "Company": company,
                "Date": pd.to_datetime(entry["Date"]),
                "cds_flat_spread": entry["cds_flat_spread"],
            })

    df = pd.DataFrame(rows)
    df = df.sort_values(["Company", "Date"])
    return df

def market_data(path_excel: str = PATH_MARKET_INDEX_EXCEL):
    path = Path(__file__).parent / path_excel
    df = pd.read_excel(path)
    return df

if __name__ == "__main__":
    df = spreads_to_df()
    print(df.head())