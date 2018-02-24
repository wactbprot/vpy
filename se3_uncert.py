import sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.sim import Sim
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal

def main():
    io = Io()
    sim = Sim("se3")
    doc = sim.build()

    res = Analysis(doc)
    unc = Uncert(doc)
    cal = Cal(doc)

    cal.pressure_fill(res)
    cal.get_add_ratio(res)
    unc.gen_val_dict(res)
    unc.gen_val_array(res)
    unc.uncert_v_start(res)
    unc.uncert_v_5(res)
    unc.uncert_p_fill(res)

    u_1 = res.pick("Uncertainty", "v_start", "1")
    u_2 = res.pick("Uncertainty", "v_5", "1")
    u_3 = res.pick("Uncertainty", "p_fill", "1")
    u_t = np.sqrt(np.power(u_1, 2) +np.power(u_3, 2) +np.power(u_3, 2) )
    io.log.info(" Uncertainty u_V_start: {}".format(u_1))
    io.log.info(" Uncertainty u_V_5: {}".format(u_2))
    io.log.info(" Uncertainty u_pfill: {}".format(u_3))
    io.log.info(" Uncertainty u_total: {}".format(u_t))

if __name__ == "__main__":
    main()
