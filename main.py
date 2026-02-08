import json
import pandas as pd
from cds_engine import EngineParams, CDSPipeLine
from cds_pricing_functions import *

def main():
    with open("data/rating_data.json", "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data["Data"])

    params = EngineParams(
        T = 5,          # 5-year CDS
        r = 0.02,       # Risk-free rate
        recovery=0.4,   # Recovery rate
        coupon=0.05,    # 500 bp
        freq=4,         # 4 payments per year
    )
    cds = CDSPipeLine(params)


    def pick_rating(row):
        for col in [
            "RATING",
            "RTG_SP_LT_LC_ISSUER_CREDIT",
            "RTG_MOODY_LONG_TERM",
            "RTG_EGAN_JONES_LOCAL_SR_UNSEC",
        ]:
            val = row.get(col)
            if pd.notna(val) and str(val).lower() != "nan":
                return str(val).strip()        
        return None


    df["rating_raw"] = df.apply(pick_rating, axis=1)
    df["rating"] = df["rating_raw"].apply(coarse_rating)
    df = df.dropna(subset=["rating", "Wgt"])

    result = cds.index_from_components(df)
    print(result)

def main2():
    from pathlib import Path
    path = Path(__file__).parent / "CDS_Spread_From_components.xlsx"
    df_excel = pd.read_excel(path)
    
    pipeline = CDSPipeLine(
    EngineParams(
        T = 5,          # 5-year CDS
        r = 0.02,       # Risk-free rate
        recovery=0.4,   # Recovery rate
        coupon=500,    # 500 bp
        freq=4,         # 4 payments per year
    ))
    result =  pipeline.index_advanced_from_excel(df_excel)
    print(result)

if __name__ == "__main__":
    main2()