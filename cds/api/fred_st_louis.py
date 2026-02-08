import pandas as pd
import matplotlib.pyplot as plt

def get_fred_data_simple(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        df = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
        df = df.dropna()        
        return df
    except Exception as e:
        print(str(e))
        return None

#BB-spread
series_id = 'BAMLH0A1HYBB'
df_fred = get_fred_data_simple(series_id)

if df_fred is not None:
    print(f"Got {len(df_fred)} rows from FRED for series {series_id}.")
    df_fred['spread_bp'] = df_fred[series_id] * 100
    
    print("\nDe senaste marknadsvärdena (i bp):")
    print(df_fred['spread_bp'].tail())

    # Plot
    df_fred['spread_bp'].plot(figsize=(10, 5), color='blue', title="ICE BofA BB US High Yield Index (bp)")
    plt.grid(True, alpha=0.3)
    plt.ylabel("Basis Points (bp)")
    plt.show()