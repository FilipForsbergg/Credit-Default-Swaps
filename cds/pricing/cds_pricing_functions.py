import json
import math
import pandas as pd
import matplotlib.pyplot as plt

from cds.pricing.pd_table import rating_to_pd
from cds.data.build_portfolio import build_portfolio_df

T = 5.0          # 5-year CDS
FREQ = 4         # quarterly payments
R = 0.02         # risk-free rate
RECOVERY = 0.40  # recovery rate


RATING_PRIORITY = [
    "RATING",
    "RTG_SP_LT_LC_ISSUER_CREDIT",
    "RTG_MOODY_LONG_TERM",
    "RTG_EGAN_JONES_LOCAL_SR_UNSEC",
]

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


def coarse_rating(rating):
    if rating not in COARSE_MAP:
        return None
    return COARSE_MAP[rating]


def first_available_rating(row, columns):
    for col in columns:
        if col not in row:
            continue

        val = row[col]
        if pd.isna(val):
            continue

        val = str(val).strip()
        if val == "":
            continue

        return val

    return None



def rating_to_hazard(rating, horizon=5):
    pd_val = rating_to_pd(rating, int(horizon))

    if pd_val is None:
        return None

    if pd_val >= 1.0:
        return float("inf")

    return -math.log(1.0 - pd_val) / horizon


def survival(lam, t):
    return math.exp(-lam * t)


def risky_pv01(T, freq, r, lam):
    dt = 1.0 / freq
    n = int(T * freq)

    pv01 = 0.0
    t_prev = 0.0
    V_prev = survival(lam, t_prev)

    for i in range(1, n + 1):
        t = i * dt
        V_t = survival(lam, t)
        pv01 += dt * math.exp(-r * t) * 0.5 * (V_prev + V_t)
        V_prev = V_t

    return pv01


def protection_leg(T, r, lam, R, steps=1000):
    dt = T / steps
    pv = 0.0

    for i in range(1, steps + 1):
        t = i * dt
        V_t = survival(lam, t)
        pv += math.exp(-r * t) * (1 - R) * lam * V_t * dt

    return pv


def fair_cds_spread(T, freq, r, lam, R):
    pv01 = risky_pv01(T, freq, r, lam)
    prot = protection_leg(T, r, lam, R)
    return prot / pv01



def main():
    df = build_portfolio_df()

    #Compute Spreads
    spreads = []

    for _, row in df.iterrows():
        rating = first_available_rating(row, RATING_PRIORITY)

        if rating is None:
            spreads.append(None)
            continue

        hazard_rate = rating_to_hazard(rating, horizon=5)

        if hazard_rate is None:
            spreads.append(None)
            continue

        s = fair_cds_spread(T, FREQ, R, hazard_rate, RECOVERY)
        spreads.append(s)

    df["spread"] = spreads

    df["RATING_CLEAN"] = df["rating"].apply(lambda x: x.strip() if isinstance(x, str) else None)
    df["RATING_COARSE"] = df["RATING_CLEAN"].apply(coarse_rating)


    #RESULTS
    df_used = df.dropna(subset=["spread"])

    wavg = (df_used["Wgt"] * df_used["spread"]).sum() / df_used["Wgt"].sum()
    print(f"Weighted average theoretical spread: {wavg*10000:.1f} bp")

    # Weighted average by rating
    rating_avg = (
        df
        .dropna(subset=["RATING_COARSE", "spread"])
        .groupby("RATING_COARSE")
        .apply(lambda x: (x["Wgt"] * x["spread"]).sum() / x["Wgt"].sum())
    )


    #plot
    ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
    rating_avg = rating_avg.reindex(ORDER)
    rating_avg_bp = 10000 * rating_avg

    plt.figure(figsize=(8, 4))
    rating_avg_bp.plot(kind="bar")
    plt.ylabel("CDS spread (basis points)")
    plt.title("CDS spreads by rating")
    plt.tight_layout()
    plt.savefig("cds_spreads_by_rating.png", bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    main()