import math
import json
import pandas as pd
from dataclasses import dataclass

from cds_pricing_functions import *

@dataclass
class EngineParams:
    T: int
    r: float
    recovery: float
    coupon: int
    freq: int


class CDSPipeLine:
    def __init__(self, params):
        self.T = params.T
        self.r = params.r
        self.recovery = params.recovery
        self.coupon = 0.05
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
    
    def diff_from_market():
        pass

    def index_from_components(self, df: pd.DataFrame):
        """
        Computes the index-spread from the average of its components
        """
        be_spreads = []

        #incase it has different weights
        weights = []

        #Calculate bond equivalent for an individual company
        for _, row in df.iterrows():
            rating = row["RATING"]
            weight = row["Wgt"]

            hazard = rating_to_hazard(rating, self.T)
            
            flat_spread = self.flat_spread(rating)
            be = self.bond_equivalent_spread(flat_spread, hazard) 

            be_spreads.append(be)
            weights.append(weight)

        # Calculate bond equivalent of the index as the average of its components
        be_index = sum(w * s for w, s in zip(weights, be_spreads)) / sum(weights)
        index_flat_spread = 2 * self.coupon - be_index

        
        return {
            "index_be_spread": be_index,
            "index_flat_spread": index_flat_spread,
        }

    def index_from_excel_inputs(self, df: pd.DataFrame):
        """
        Använder en fast diskonteringsränta rpv01
        """
        rpv01 = 4.25
        df["bond_equivalent"] = 100 - (df["cds_flat_spread"] - self.coupon) * (rpv01 / 100)

        be_index = df["bond_equivalent"].mean()
        calc_index = self.coupon*100 + (100 - be_index) / (rpv01 / 100) 

        return {
            "index_be_spread_bp": be_index,
            "index_flat_spread_bp": calc_index,
        }
    
    def index_advanced_from_excel(self, df: pd.DataFrame) -> dict[str, float]:
        be_prices = []
        for _, row in df.iterrows():
            flat_spread = row["cds_flat_spread"] / 10000
            hazard = flat_spread / (1 - self.recovery)
            pv01 = risky_pv01(self.T, self.freq, self.r, hazard)
            upfront = (flat_spread - self.coupon) * pv01
            price = 100 - (upfront * 100)

            be_prices.append(price)
        
        # average price for the index
        avg_index_price = sum(be_prices) / len(be_prices)

        # convert back to spread
        target_price = avg_index_price


        # find the spread that gives our price
        # using binary search
        low = 0.0001
        high = 1
        solved_spread = 0
        for i in range(100):
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