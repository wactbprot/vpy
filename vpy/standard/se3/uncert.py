import sys
import numpy as np
from .std import Se3

class Uncert(Se3):

    volume_unit = "cm^3"
    pressure_unit = "Pa"
    rel_unit = "1"    

    def __init__(self, doc):
        super().__init__(doc)

    # -------------------------
    ## add volume
    # -------------------------
    def sens_volume_5(self, V_5, p_0, p_1, p_r):
        return (p_1 - p_r)/(p_0 - p_1)
    
    def sens_pressure_0(self, V_5, p_0, p_1, p_r):
        return -V_5*(p_1 - p_r)/(p_0 - p_1)**2

    def sens_pressure_1(self, V_5, p_0, p_1, p_r):
        return V_5/(p_0 - p_1) + V_5*(p_1 - p_r)/(p_0 - p_1)**2
    
    def sens_pressure_r(self, V_5, p_0, p_1, p_r):
        return -V_5/(p_0 - p_1)
    
    def volume_5(self, u_V_5, V_5_unit, V_5, p_0, p_1, p_r):
        if V_5_unit == "1":
            u = u_V_5 * V_5
        elif V_5_unit == self.volume_unit:
            u = u_V_5
        else:
            msg = "wrong unit in uncert_volume_5"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_volume_5(V_5, p_0, p_1, p_r) * u
    
    def pressure_0(self, u_p_0, p_0_unit, V_5, p_0, p_1, p_r):
        if p_0_unit == self.rel_unit:
            u = u_p_0 * p_0
        elif p_0_unit == self.pressure_unit:
            u = u_p_0
        else:
            msg = "wrong unit in uncert_pressure_0"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_pressure_0(V_5, p_0, p_1, p_r) * u
    
    def pressure_1(self, u_p_1, p_1_unit, V_5, p_0, p_1, p_r):
        if p_1_unit == self.rel_unit:
            u = u_p_1 * p_1
        elif p_1_unit == self.pressure_unit:
            u = u_p_1
        else:
            msg = "wrong unit in uncert_pressure_1"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_pressure_1(V_5, p_0, p_1, p_r) * u
    
    def pressure_r(self, u_p_r, p_r_unit, V_5, p_0, p_1, p_r):
        if p_r_unit == self.rel_unit:
            u = u_p_r * p_r
        elif p_r_unit == self.pressure_unit:
            u = u_p_r
        else:
            msg = "wrong unit in uncert_pressure_r"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_pressure_r(V_5, p_0, p_1, p_r) * u
    
    # -------------------------
    ## vaclab cmc records
    # -------------------------
    def cmc(self, ana):
        p_list = ana.pick("Pressure", "cal", self.pressure_unit)
        
        u = np.asarray([np.piecewise(p, [p <= 0.027, (p > 0.027 and p <= 0.3), (p > 0.3 and p <= 0.73), (p >0.73 and p <= 9.), (p > 9. and p <= 1000.), (p > 1000. and p <= 8000.),  8000. < p]
                                       ,[0.0014,                        0.001,                 0.00092,              0.00086,                 0.00075,                   0.00019,  0.00014] ).tolist() for p in p_list])

        ana.store("Uncertainty", "standard", u , "1")

