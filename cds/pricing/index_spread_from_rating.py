import json
import pandas as pd
import numpy as np
from cds.data.build_portfolio import build_rating_df
from cds.pricing.cds_engine import CDSPipeLine, EngineParams
from cds.pricing.cds_pricing_functions import *

def main():
    df = build_rating_df()
    params = EngineParams(
        T=5,
        r=0.02,
        recovery=0.4,
        coupon=0.05,
        freq=4,
    )
    pipeline = CDSPipeLine(params)

    df['cds_flat_spread'] = df['RATING'].apply(
        lambda x: pipeline.flat_spread(x) * 10000
    )
    adv_result = pipeline.index_from_components_advanced(df)
    
    tot_flat = 0
    for _, company in df.iterrows():
        rating = company['RATING']
        flat_spread = pipeline.flat_spread(rating) * 10000
        tot_flat += flat_spread
    
    result = tot_flat / len(df)

    print(f"Advanced result: {adv_result}")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()