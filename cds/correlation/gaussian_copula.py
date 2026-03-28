import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from pathlib import Path
from cds.pricing.cds_pricing_functions import fair_cds_spread
from cds.data.build_portfolio import build_portfolio_df
from cds.pricing.cds_engine import CDS


def spreads_to_pd(df_day, T, recovery):
    spreads = df_day["cds_flat_spread"].values / 10000
    lambdas = spreads / (1 - recovery)
    Q_T = 1 - np.exp(-lambdas * T)
    return Q_T

def conditional_pd(Q_T: np.ndarray, rho, alpha):
    """
    One-factor Gaussian copula conditional PD.
    alpha is the market-stress quantile, e.g. 0.05.
    """
    eps = 1e-10
    Q_T = np.clip(Q_T, eps, 1 - eps)

    F_alpha = norm.ppf(alpha)
    K = norm.ppf(Q_T)

    num = K - np.sqrt(rho) * F_alpha
    den = np.sqrt(1.0 - rho)

    return norm.cdf(num / den)


def pd_to_spreads_bp(Q_cond, T, r, recovery, freq):
    eps = 1e-10
    Q_cond = np.clip(Q_cond, eps, 1-eps)
    lambdas = -np.log(1-Q_cond) / T
    
    spreads_bp = []
    for lam in lambdas:
        s = fair_cds_spread(T, freq, r, lam, recovery)
        spreads_bp.append(s * 10000)

    return np.array(spreads_bp)  


def model_index_spread_from_rho(df_day, rho, alpha, cds):
    Q_T = spreads_to_pd(df_day, cds.T, cds.recovery)
    Q_cond = conditional_pd(Q_T, rho, alpha)
    stressed_spreads_bp = pd_to_spreads_bp(
        Q_cond, cds.T, cds.r, cds.recovery, cds.freq
    )

    df_tmp = df_day.copy()
    df_tmp["cds_flat_spread"] = stressed_spreads_bp

    res = cds.index_from_component_spreads(df_tmp)
    return res["index_flat_calc_bp"]

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

#def model_index_spread_from_rho(df_day, rho, alpha, cds: CDS):
#
#    Q_T = spreads_to_pd(df_day, cds.T, cds.recovery)
#
#    Q_cond = conditional_pd(Q_T, rho, alpha)
#    lambdas = -np.log(1 - Q_cond) / cds.T
#
#    spreads = []
#
#    for lam in lambdas:
#        s = fair_cds_spread(cds.T, cds.freq, cds.r, lam, cds.recovery)
#        spreads.append(s)
#
#    df_temp = df_day.copy()
#    df_temp["cds_flat_spread"] = np.array(spreads) * 10000
#
#    res = cds.index_from_component_spreads(df_temp)
#
#    return res["index_flat_calc_bp"]

def implied_rho(df_day, market_spread_bp, cds, alpha=0.05, tol = 1e-4, max_iter=60):
    low, high = 0.0, 0.95

    s_low = model_index_spread_from_rho(df_day, low, alpha, cds)
    s_high = model_index_spread_from_rho(df_day, high, alpha, cds)

    # If market is below rho=0 model, set rho=0
    if market_spread_bp <= s_low:
        return 0.0

    # If market is above rho=high model, cap at high
    if market_spread_bp >= s_high:
        return high

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        s_mid = model_index_spread_from_rho(df_day, mid, alpha, cds)

        if abs(s_mid - market_spread_bp) < tol:
            return mid

        if s_mid < market_spread_bp:
            low = mid
        else:
            high = mid
    
    print(f"Iterations: {_}")
    return 0.5 * (low + high)


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