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

    print(res.pick("Uncertainty", "u_V_start", "mbar"))
if __name__ == "__main__":
    main()
