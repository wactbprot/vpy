import sys
import numpy as np
from vpy.analysis import Analysis
from vpy.sim import Sim
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal

def main():
    sim = Sim("se3")
    doc = sim.build()

    res = Analysis(doc)
    unc = Uncert(doc)
    cal = Cal(doc)

    cal.pressure_fill(res)
    unc.gen_val_dict(res)
    unc.gen_val_array(res)
    unc.uncert_v_start(res)
    unc.uncert_v_5(res)

    u_V_start = res.pick("Uncertainty", "u_V_start", "1")
    u_V_5     = res.pick("Uncertainty", "u_V_5", "1")

if __name__ == "__main__":
    main()
