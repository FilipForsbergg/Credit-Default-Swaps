import pandas as pd
from dataclasses import dataclass
from cds.pricing.cds_pricing_functions import *

@dataclass
class Params:
    T: int
    r: float
    recovery: float
    coupon: int
    freq: int

class CDS:
    def __init__(self, params: Params):
        self.T = params.T
        self.r = params.r
        self.recovery = params.recovery
        self.coupon = params.coupon
        self.freq = params.freq
    
    def hazard_from_rating(self, rating):
        hazard = rating_to_hazard(rating, self.T)
        if hazard is None:
            raise ValueError("Hazard rate is None!")
        return hazard

    def flat_spread(self, rating: str) -> float:
        """
        Calculates the cds flat spread for a given credit-rating
        
        :param rating: Credit rating of the company
        """
        hazard_rate = self.hazard_from_rating(rating)
        return fair_cds_spread(
            self.T, self.freq, self.r, hazard_rate, self.recovery
        )


    def upfront(self, flat_spread: float, hazard: float) -> float:
        pv01 = risky_pv01(self.T, self.freq, self.r, hazard)
        upfr = (self.coupon - flat_spread) * pv01
        return upfr


    def bond_equivalent_spread(self, flat_spread, hazard_rate):
        upfr = self.upfront(flat_spread, hazard_rate)
        pv01 = risky_pv01(self.T, self.freq, self.r, hazard_rate)
        be = upfr / pv01 + self.coupon
        return be


    def index_from_component_spreads(self, df: pd.DataFrame) -> dict[str, float]:
        be_prices = []
        for _, row in df.iterrows():
            flat_spread = row["cds_flat_spread"] / 10000
            hazard = flat_spread / (1 - self.recovery)
            pv01 = risky_pv01(self.T, self.freq, self.r, hazard)
            upfront = (flat_spread - self.coupon) * pv01
            price = 100 - (upfront * 100)
            be_prices.append(price)
        avg_index_price = sum(be_prices) / len(be_prices)

        # find the spread that gives our price
        target_price = avg_index_price
        low = 0.0001
        high = 1
        solved_spread = 0
        for _ in range(100):
            mid = (low + high) / 2
            h_guess = mid /  (1 - self.recovery)
            pv01_guess = risky_pv01(self.T, self.freq, self.r, h_guess)

            upfront_guess = (mid - self.coupon) * pv01_guess
            price_guess = 100 - (upfront_guess * 100)
            
            if price_guess < target_price:
                # If the price is to low (too cheap), the spread is to high (too risky)
                high = mid
            else:
                low = mid
            
        solved_spread = (low + high) / 2
        return {
            "index_price_avg": float(avg_index_price),
            "index_flat_calc_bp": float(solved_spread * 10000),
        }
    
    def spreads_from_rating(self, df: pd.DataFrame) -> pd.DataFrame:
        df["cds_flat_spread"] = df["RATING"].apply(
            lambda x: self.flat_spread(x) * 10000
        )
        return df 

    def index_spread_from_component_ratings(self, df: pd.DataFrame) -> dict[str, float]:
        df["cds_flat_spread"] = df["RATING"].apply(
            lambda x: self.flat_spread(x) * 10000
        )
        
        adv_spread = self.index_from_component_spreads(df)
        spread = df["cds_flat_spread"].mean()
        
        return {"adv_spread": adv_spread,"spread": spread} 