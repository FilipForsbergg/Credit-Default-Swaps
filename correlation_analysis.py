import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

from cds.pricing.pd_table import rating_to_pd  # rating -> PD(T)

T = 5  # years
RECOVERY = 0.40

RATING_COL = "RATING"
WEIGHT_COL = "Wgt"

COARSE_MAP = {
    "AAA": "AAA",
    "AA+": "AA", "AA": "AA", "AA-": "AA",
    "A+": "A", "A": "A", "A-": "A",
    "BBB+": "BBB", "BBB": "BBB", "BBB-": "BBB",
    "BB+": "BB", "BB": "BB", "BB-": "BB",
    "B+": "B", "B": "B", "B-": "B",
    "CCC+": "CCC", "CCC": "CCC", "CCC-": "CCC",
    "CC": "CCC", "C": "CCC", "D": "CCC",
}

def coarse_rating(x):
    if x is None:
        return None
    x = str(x).strip()
    return COARSE_MAP.get(x)

def build_portfolio_df(path_json: str) -> pd.DataFrame:
    with open(path_json, "r") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw["Data"])

    df[WEIGHT_COL] = pd.to_numeric(df[WEIGHT_COL], errors="coerce")
    df = df.dropna(subset=[WEIGHT_COL, RATING_COL]).copy()
    df["rating_coarse"] = df[RATING_COL].apply(coarse_rating)
    df = df.dropna(subset=["rating_coarse"])

    # Q_i(T) from rating table
    df["Q_T"] = df["rating_coarse"].apply(lambda r: rating_to_pd(r, T))
    df = df.dropna(subset=["Q_T"])

    df["w"] = df[WEIGHT_COL] / df[WEIGHT_COL].sum()

    return df[["rating_coarse", "Q_T", "w"]].reset_index(drop=True)

def conditional_default_prob(Q_T: np.ndarray, F: np.ndarray, rho: float) -> np.ndarray:
    """
    K_i = N^{-1}(Q_i(T))
    Q_i(T|F) = N((K_i - sqrt(rho) F)/sqrt(1-rho))
    Shapes:
      Q_T: (n_names,)
      F:   (n_sims,)
    Returns:
      Q_cond: (n_sims, n_names)
    """
    K = norm.ppf(Q_T)  # (n_names,)
    num = K[None, :] - np.sqrt(rho) * F[:, None]
    den = np.sqrt(1.0 - rho)
    return norm.cdf(num / den)

def loss_distribution(df_port: pd.DataFrame, rho: float, n_sims: int = 200_000, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    F = rng.standard_normal(n_sims)  # common factor (market factor)

    Q_T = df_port["Q_T"].to_numpy()
    w = df_port["w"].to_numpy()

    Q_cond = conditional_default_prob(Q_T, F, rho)  # (n_sims, n_names)
    L = (1.0 - RECOVERY) * (Q_cond @ w)             # (n_sims,)
    return L

def summarize_losses(L: np.ndarray, alpha: float = 0.99) -> dict:
    var = np.quantile(L, alpha)
    es = L[L >= var].mean()
    return {
        "EL": float(L.mean()),
        f"VaR_{int(alpha*100)}": float(var),
        f"ES_{int(alpha*100)}": float(es),
    }

def main():
    df_port = build_portfolio_df("cds/data/rating_data.json")

    rhos = [0.0, 0.1, 0.2, 0.3, 0.5]
    results = []

    # VaR vs rho
    for rho in rhos:
        L = loss_distribution(df_port, rho=rho, n_sims=100_000, seed=42)
        stats = summarize_losses(L, alpha=0.99)
        stats["rho"] = rho
        results.append(stats)

    res = pd.DataFrame(results).set_index("rho")
    print(res)

    plt.figure(figsize=(7,4))
    plt.plot(res.index, 100 * res["VaR_99"], marker="o")
    plt.xlabel("rho (default correlation)")
    plt.ylabel("Portfolio loss VaR 99% (%) over T years")
    plt.title("Tail loss increases with default correlation")
    plt.tight_layout()
    plt.show()

    # Fördelning för 2st rho
    for rho in [0.0, 0.3]:
        L = loss_distribution(df_port, rho=rho, n_sims=200_000, seed=1)
        plt.figure(figsize=(7,4))
        plt.hist(100*L, bins=80, density=True)
        plt.xlabel("Portfolio loss (%) over T years")
        plt.ylabel("Density")
        plt.title(f"Loss distribution, rho={rho}")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
