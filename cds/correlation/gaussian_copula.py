import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from pathlib import Path
from cds.pricing.cds_pricing_functions import fair_cds_spread
from cds.data.build_portfolio import build_portfolio_df

def conditional_pd(Q_T: np.ndarray, rho, alpha):
    F_alpha = norm.ppf(alpha)
    K = norm.ppf(Q_T)

    numerator = K - np.sqrt(rho) * F_alpha
    denominator = np.sqrt(1 - rho)
    return norm.cdf(numerator / denominator)

def hazard_from_cum_pd(Q_T: np.ndarray, T):
    return -np.log(1 - Q_T) / T

def index_spread_with_correlation(df, rho, alpha, T, r, recovery, freq):
    Q_T = df["Q_T"].values
    weights = df["w"].values
    
    # Gaussian copula stress adjustment
    Q_stress = conditional_pd(Q_T, rho, alpha)
    lambdas = hazard_from_cum_pd(Q_stress, T)

    # Compute single-name spreads
    spreads = []
    for lam in lambdas:
        s = fair_cds_spread(T, freq, r, lam, recovery)
        spreads.append(s)
    spreads = np.array(spreads)

    index_spread = np.sum(weights * spreads)
    return index_spread

def correlation_plot(rating_spread, mild, medium, stress):
    """
    rating_spread: index spread calculated from credit-rating
    args: list of index spreads calculated from different correlation levels
    """
    market_timeseries_path = Path(__file__).resolve().parent.parent / "data" / "timeserieItems.xlsx"
    market_df = pd.read_excel(market_timeseries_path)
    market_df["date"] = pd.to_datetime(market_df["date"])
    market_df = market_df.sort_values("date")

    plt.figure(figsize=(10,6))

    # Market-index
    plt.plot(market_df["date"], market_df["value"]*10000)
    
    # Horizontal correlation lines
    #Stressed
    plt.axhline(
        stress,
        color="red",
        linestyle="--",
        label=f"Stressed"
    )
    
    #Medium
    plt.axhline(
        medium,
        color="purple",
        linestyle="--",
        label="Medium"
    )


    #Mild
    plt.axhline(
        mild,
        color="orange",
        linestyle="--",
        label="Mild"
    )

    
    #Uncorrelated
    plt.axhline(
        rating_spread,
        color="blue",
        linestyle="--",
        label="Rating-based spread"
    )
    
    
    plt.xlabel("Date")
    plt.ylabel("Index Value")
    plt.title("Market Index Over Time")
    plt.tight_layout()
    plt.show()

def main() -> None:
    df = build_portfolio_df()
    s_uncorr = index_spread_with_correlation(df, rho=0.0, alpha=0.5, T=5, r=0.02, recovery=0.4, freq=4) * 10000
    s_corr_mild = index_spread_with_correlation(df, rho=0.3, alpha=0.1, T=5, r=0.02, recovery=0.4, freq=4) * 10000
    s_corr_medium = index_spread_with_correlation(df, rho=0.4, alpha=0.05, T=5, r=0.02, recovery=0.4, freq=4) * 10000
    s_corr_stress = index_spread_with_correlation(df, rho=0.5, alpha=0.01, T=5, r=0.02, recovery=0.4, freq=4) * 10000
    
    correlation_plot(
        rating_spread=s_uncorr,
        mild=s_corr_mild,
        medium=s_corr_medium,
        stress=s_corr_stress
    )

if __name__ == "__main__":
    main()