"""
Evaluation of small expansion ratio f_s
measurement.

run:

$[vpy]> python se3_expansion_eval_fs.py --id "cal-2017-se3|frs5-vg-1001_0007"
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

from vpy.pkg_io import Io
from vpy.analysis import Analysis

from vpy.values import Pressure, AuxValues

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
        ## pressure_cal runs all necessary methods
        frs_calc.pressure_cal(res)

        frs_uncert.total(res)

        # SE3:
        se3_calc = Se3Calc(doc)

        se3_calc.temperature_before(res)
        se3_calc.temperature_after(res)
        se3_calc.temperature_room(res)
        se3_calc.pressure_fill(res)
        se3_calc.expansion(res)
        se3_calc.volume_start(res)
        se3_calc.volume_add(res)
        se3_calc.real_gas_correction(res)

        # se3 uncert
        se3_uncert = Se3Uncert(doc)
        se3_uncert.gen_val_dict(res)
        se3_uncert.gen_val_array(res)
        se3_uncert.pressure_fill(res)
        se3_uncert.temperature_after(res)
        se3_uncert.temperature_before(res)


        rg = res.pick("Correction", "rg", "1")
        p_0 = res.pick("Pressure", "fill", "mbar")
        p_1 = res.pick("Pressure", "frs5", "mbar")
        T_0 = res.pick("Temperature", "before", "K")
        T_1 = res.pick("Temperature", "after", "K")

        ## null indicator:
        pres = Pressure(doc)
        auxval = AuxValues(doc)
        p_nd_offset_before = auxval.get_value("nd_offset_before", "mbar")
        p_nd_offset_after = auxval.get_value("nd_offset_after", "mbar")
        p_nd_offset = (p_nd_offset_before + p_nd_offset_after )/2

        p_nd_ind = pres.get_value("nd_ind", "mbar")
        res.store("Pressure", "nd", p_nd_ind - p_nd_offset, "mbar")
        u_nd_rel = 1.0e-2
        res.store("Uncertainty", "nd", np.abs(p_nd_ind  * u_nd_rel), "1")
        p_nd = res.pick("Pressure", "nd", "mbar")

        p_after = (p_1 - p_nd)

        g_after = np.full(len(p_after), 0.0)
        g_before = np.full(len(p_after), 0.0)
        for i in range(len(p_after)):
            if i == 0:
                g_after[i] = p_after[i] / T_1[i]
                g_before[i] = (p_0[i] * rg[i]) / T_0[i]
            else:
                g_after[i] = p_after[i] / T_1[i]
                #g_before[i] = (p_0[i] * rg[i]) / T_0[i] + g_before[i-1]
                g_before[i] =  (g_before[i-1] * T_0[i-1] +  (p_0[i] * rg[i])) / T_0[i]

        f_s = np.mean(g_after/g_before)
        u_ex = np.std(g_after/g_before)/f_s
        print(f_s)
        print(u_ex)
        # nd uncert


        u_1 = res.pick("Uncertainty", "p_fill", "1")
        u_2 = res.pick("Uncertainty", "t_before", "1")
        u_3 = res.pick("Uncertainty", "t_after", "1")
        u_4 = res.pick("Uncertainty", "nd", "1")
        u_5 = res.pick("Uncertainty", "frs5_total_rel", "1")

        u_t = np.sqrt(u_1**2 + u_2**2 + u_3**2 + u_4**2+ u_5**2)
        res.store("Uncertainty", "total", u_t, "1")

        u = 0
        for u_i in u_t:
            if u == 0:
                u = 1/u_i**2
            else:
                u = u +1/u_i**2

        u_sys = 1/u**0.5
        print((u_ex**2 + u_sys**2)**0.5)

        V_s = 20.69

        print(V_s*(1/f_s -1))

        io.save_doc(res.build_doc())


if __name__ == "__main__":
    main()
