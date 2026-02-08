import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from cds.pricing.cds_engine import EngineParams, CDSPipeLine

def generate_time_series_basis(file_path, days=30):
    df_orig = pd.read_excel(file_path)
    
    params = EngineParams(T=5, r=0.02, recovery=0.4, coupon=500, freq=4)
    pipeline = CDSPipeLine(params)
    
    history = []
    
    current_market_index = 244.37     
    print(f"Simulerar {days} dagar av mock-data")
    
    for day in range(days):
        noise = np.random.normal(1, 0.02, len(df_orig))
        df_daily = df_orig.copy()
        df_daily["cds_flat_spread"] = df_daily["cds_flat_spread"] * noise
        
        result = pipeline.index_from_components_advanced(df_daily)
        model_spread = result["index_flat_calc_bp"]
        current_market_index += np.random.normal((model_spread - current_market_index)*0.1, 2.0)
        
        basis = current_market_index - model_spread
        
        history.append({
            "Day": day,
            "Model_Spread": model_spread,
            "Market_Spread": current_market_index,
            "Basis": basis
        })

    return pd.DataFrame(history)

path = Path(__file__).parent / "CDS_Spread_From_components.xlsx"
df_history = generate_time_series_basis(path)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

ax1.plot(df_history["Day"], df_history["Market_Spread"], label="Market Index (Observed)", color="#1f77b4", linewidth=2)
ax1.plot(df_history["Day"], df_history["Model_Spread"], label="Model Index (Fair Value)", color="#2ca02c", linestyle="--")
ax1.set_ylabel("Spread (bp)")
ax1.set_title("CDS Index: Market vs Theoretical Fair Value")
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.fill_between(df_history["Day"], df_history["Basis"], 0, 
                 where=(df_history["Basis"] >= 0), facecolor='green', alpha=0.3, label="Positive Basis")
ax2.fill_between(df_history["Day"], df_history["Basis"], 0, 
                 where=(df_history["Basis"] < 0), facecolor='red', alpha=0.3, label="Negative Basis")
ax2.axhline(0, color='black', linewidth=1)
ax2.set_ylabel("Basis (bp)")
ax2.set_xlabel("Days")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()