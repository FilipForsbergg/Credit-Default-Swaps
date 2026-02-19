import json
import pandas as pd
import numpy as np
from cds.data.build_portfolio import build_rating_df
from cds.pricing.cds_engine import CDSPipeLine, EngineParams
from cds.pricing.cds_pricing_functions import *

import matplotlib.pyplot as plt

def plot_spreads(df):
    df_plot = df.drop_duplicates(subset=['RATING']).sort_values(by='cds_flat_spread')
    plt.figure(figsize=(6, 4))
    bars = plt.bar(df_plot['RATING'], df_plot['cds_flat_spread'], color='skyblue')
    
    plt.xlabel("Rating")
    plt.ylabel("Flat Spread (bps)")
    plt.title("CDS Flat Spread per Rating (Itraxx XOVER)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 1), 
                 ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig("cds_spread_plot.png")
    plt.show()

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
    plot_spreads(df)


    print(f"Advanced result: {adv_result}")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()