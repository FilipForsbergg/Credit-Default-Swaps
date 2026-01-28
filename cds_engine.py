import math
import json
import pandas as pd
from dataclasses import dataclass

from cds_pricing_functions import *

@dataclass
class EngineParams:
    T: int
    r: int
    recovery: int
    coupon: int
    freq: int


class CDSPipeLine:
    def __init__(self, params):
        self.T = params.T
        self.r = params.r
        self.recovery = params.recovery
        self.coupon = params.coupon
        self.freq = params.freq

    def flat_spread(self, rating: str) -> float:
        """
        Calculates the cds flat spread for a given credit-rating
        
        :param rating: Credit rating of the company
        """
        hazard_rate = rating_to_hazard(rating, self.T)
        if hazard_rate is None:
            raise ValueError("Hazard rate is None!")
        return fair_cds_spread(self.T, self.freq, self.r, hazard_rate, self.recovery)


    def upfront(self, flat_spread: float, rating: str) -> float:
        hazard = rating_to_hazard(rating, self.T)
        upfr = (self.coupon - flat_spread) * risky_pv01(self.T, self.freq, self.r, hazard)
        return upfr


    def bond_equivalent_spread(self, flat_spread, hazard_rate):
        upfr = self.upfront(flat_spread, hazard_rate)
        riskypv01 = risky_pv01(self.T, self.freq, self.r, hazard_rate)
        be = upfr / riskypv01 + self.coupon
        return be
    
    def index_from_components(self, df: pd.DataFrame):
        """
        Replicates the index-spread from its components
        """
        be_spreads = []

        #Calculate bond equivalent for an individual company
        for _, row in df.iterrows():
            rating = row["RATING"]
            hazard = rating_to_hazard(rating)
            
            flat_spread = self.flat_spread(rating)
            be = self.bond_equivalent_spread(flat_spread, hazard) 
            
            be_spreads.append(be)
        
        # Calculate bond equivalent of the index as the average of its components
        be_index = sum(be_spreads) / len(be_spreads)
        index_flat_spread = 2 * self.coupon - be_index

        return {
            "index_be_spread": be_index,
            "index_flat_spread": index_flat_spread,
        }


