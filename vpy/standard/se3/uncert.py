import sys
import numpy as np
import sympy as sym
from .std import Se3


class Uncert(Se3):

    def __init__(self, doc):
        super().__init__(doc)

   
    def cmc(self, ana):
        p_list = ana.pick("Pressure", "cal", "Pa")
        
        u = np.asarray([np.piecewise(p, [p <= 0.027, (p > 0.027 and p <= 0.3), (p > 0.3 and p <= 0.73), (p >0.73 and p <= 9.), (p > 9. and p <= 1000.), (p > 1000. and p <= 8000.),  8000. < p]
                                       ,[0.0014,                        0.001,                 0.00092,              0.00086,                 0.00075,                   0.00019,  0.00014] ).tolist() for p in p_list])

        ana.store("Uncertainty", "standard", u , "1")

