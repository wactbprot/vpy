"""
Evaluation of small expansion ratio f_s
measurement.

run:

$[vpy]> python se3_expansion_eval_fs.py --id "cal-2017-se3|frs5-vg-1001_0007"
"""

import sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal as FrsCalc
from vpy.standard.frs5.uncert import Uncert as FrsUncert
from vpy.standard.se3.cal import Cal as Se3Calc
from vpy.standard.se3.uncert import Uncert as Se3Uncert



def main():
    io = Io()
    doc = io.load_doc()

    if doc:
        res = Analysis(doc)

        # FRS5:
        frs_calc = FrsCalc(doc)
        frs_uncert = FrsUncert(doc)

        frs_calc.temperature(res)
        frs_calc.pressure_res(res)
        frs_calc.pressure_cal(res)

        frs_uncert.total(res)

        # SE3:
        se3_calc = Se3Calc(doc)

        se3_calc.temperature_before(res)
        se3_calc.temperature_after(res)
        se3_calc.temperature_room(res)
        se3_calc.pressure_fill(res)
        se3_calc.real_gas_correction(res)

        # se3 uncert
        se3_uncert = Se3Uncert(doc)
        se3_uncert.gen_val_dict(res)
        se3_uncert.gen_val_array(res)
        se3_uncert.pressure_fill(res)
        se3_uncert.temperature_after(res)
        se3_uncert.temperature_before(res)

        ## null indicator:
        ## ..next..



        rg = res.pick("Correction", "rg", "1")
        p_0 = res.pick("Pressure", "fill", "mbar")
        p_1 = res.pick("Pressure", "frs5", "mbar")
        p_nd = res.pick("Pressure", "nd", "mbar")
        T_0 = res.pick("Temperature", "before", "K")
        T_1 = res.pick("Temperature", "after", "K")

        cor_tem = T_0 / T_1
        f = (p_1 - p_nd) / (p_0 * rg) * cor_tem

        res.store("Correction", "temperature_expansion", cor_tem, "1")
        res.store("Expansion", se3_calc.get_expansion()[-1], f, "1")
        log.info("expansion factors are: {}".format(f))
        log.info("mean value: {}".format(np.nanmean(f)))
        log.info("standard deviation of mean value: {}".format(
            np.nanstd(f) / np.nanmean(f) / np.sqrt(len(f))))

        # nd uncert
        u_nd_rel = 1.0e-2
        res.store("Uncertainty", "nd", p_nd * u_nd_rel / p_1, "1")

        u_1 = res.pick("Uncertainty", "p_fill", "1")
        u_2 = res.pick("Uncertainty", "t_before", "1")
        u_3 = res.pick("Uncertainty", "t_after", "1")
        u_4 = res.pick("Uncertainty", "nd", "1")

        u_t = np.sqrt(u_1**2 + u_2**2 + u_3**2 + u_4**2)
        res.store("Uncertainty", "total", u_t, "1")

        io.save_doc(res.build_doc())


if __name__ == "__main__":
    main()
