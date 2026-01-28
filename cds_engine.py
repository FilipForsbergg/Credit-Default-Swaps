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
    
    def diff_from_market():
        pass

    def index_from_components(self, df: pd.DataFrame):
        """
        Replicates the index-spread from its components
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
        be_index_avr = sum(be_spreads) / len(be_spreads)
        index_flat_spread_avr = 2 * self.coupon - be_index_avr

        
        return {
            "index_be_spread": be_index_avr,
            "index_flat_spread": index_flat_spread_avr,
        }


