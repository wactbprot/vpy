import numpy as np
import copy
import sympy as sym
from .std import Ce3


class Cal(Ce3):
    ## sd of the gn cdgs must be better than:

    np.warnings.filterwarnings('ignore')

    def __init__(self, doc):
        super().__init__(doc)

    def pressure_fill(self, ana):
        p_target = self.Pres.get_value("target_pressure", "Pa")
        print(p_target)
