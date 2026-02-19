import json
import pandas as pd
from pathlib import Path

from cds.pricing.cds_engine import EngineParams, CDSPipeLine
from cds.pricing.cds_pricing_functions import *

def main():
    path = Path(__file__).parent / "CDS_Spread_From_components.xlsx"
    df_excel = pd.read_excel(path)
    
    params = EngineParams(
        T = 5,          # 5-year CDS
        r = 0.02,       # Risk-free rate
        recovery=0.4,   # Recovery rate
        coupon=500,     # 500 bp
        freq=4,         # 4 payments per year
    )
    pipeline = CDSPipeLine(params)
    result =  pipeline.index_from_components_advanced(df_excel)
    print(result)

if __name__ == "__main__":
    main()