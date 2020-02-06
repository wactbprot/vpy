"""
Evaluation of small expansion ratio f_s
measurement.

run:

$[vpy]> python script/se3/se3_expansion_eval_fs.py --id "cal-2019-se3|frs5-vg-1001_0001"

see http://a73435.berlin.ptb.de:82/lab/tree/QS/QSE-SE3-20-4-f_s.ipynb

"""

import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])
import numpy as np
import matplotlib.pyplot as plt

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.constants import Constants

from vpy.values import Pressure, AuxValues, Time, Values

from vpy.standard.frs5.cal import Cal as FrsCalc
from vpy.standard.frs5.uncert import Uncert as FrsUncert
from vpy.standard.se3.cal import Cal as Se3Calc
from vpy.standard.se3.uncert import Uncert as Se3Uncert
from vpy.device.cdg import Cdg


def main():
    io = Io()
    io.eval_args()
    doc = io.load_doc()
    unit = "Pa"
    if doc:

        ## save the doc in ana.org
        res = Analysis(doc, analysis_type = 'expansion')
        const = Constants(doc=doc)
        val = Values({})

        ## -------------------------
        ## SE3
        ## -------------------------
        base_doc_se3 = io.get_base_doc("se3")
        se3_doc = io.update_cal_doc(doc, base_doc_se3)
        
        se3_calc = Se3Calc(se3_doc)
        uncert_se3 = Se3Uncert(se3_doc)

        f_names = se3_calc.get_expansion_name()
        f_name = f_names[0] 

        se3_calc.temperature_before(res)
        se3_calc.temperature_after(res)
        se3_calc.temperature_room(res)

        se3_calc.pressure_gn_corr(res)
        se3_calc.pressure_gn_mean(res) 
        se3_calc.expansion(res)
        se3_calc.time_meas(res)
        se3_calc.real_gas_correction(res)

        rg = res.pick("Correction", "rg", "1")
        p_0 = res.pick("Pressure", "fill", "Pa")
        p_1 = res.pick("Pressure", "cal", "Pa")
        T_0 = res.pick("Temperature", "before", "K")
        T_1 = res.pick("Temperature", "after", "K")
        
        u_p_0 = uncert_se3.contrib_pressure_fill(p_0, unit, skip_type="A")
        u_T_1 = uncert_se3.contrib_temperature_vessel(T_1, "K" , skip_type="A")
        u_T_0 = uncert_se3.contrib_temperature_volume_start(T_0, "K", f_names,  skip_type="A")

        res.store("Pressure", "fill", p_0, unit)
        res.store("Uncertainty", "fill", u_p_0, unit)
        res.store("Temperature", "before", T_0, "K")
        res.store("Temperature", "after", T_1, "K")
        res.store("Uncertainty", "before", u_T_0, "K")
        res.store("Uncertainty", "after", u_T_1, "K")
        res.store("Correction", "rg", rg,  "1")

        ## old Standard section does not have delta_heigth
        ## values
        ## dh correction for f_s = 0.9999609272217588
        dh = 0.9999609272217588
        res.store("Correction", "delta_heigth" , np.full(len(p_0), dh) ,  "1")
        
        ## -------------------------
        ## frs5
        ## -------------------------
        base_doc_frs5 = io.get_base_doc("frs5")
        frs_doc = io.update_cal_doc(doc, base_doc_frs5)
        cal_frs = FrsCalc(frs_doc)  
        uncert = FrsUncert(frs_doc)
        
        cal_frs.temperature(res)
        cal_frs.pressure_res(res)
        cal_frs.pressure_cal(res)            
        uncert.total_standard(res, no_type_a=True)
        
        p_1 = res.pick("Pressure", "cal", unit)
        u_p_1 = res.pick("Uncertainty", "standard", "1")*p_1

        res.store("Pressure", "cal", p_1, unit)
        res.store("Uncertainty", "cal", u_p_1*p_1, unit)

        ## -------------------------
        ## p_nd
        ## ------------------------- 
        pres = Pressure(doc)
        auxval = AuxValues(doc)
        time = Time(doc)

        p_nd_offset_before = auxval.get_value("nd_offset_before", "mbar")
        p_nd_offset_after = auxval.get_value("nd_offset_after", "mbar")
        if p_nd_offset_after:
            p_nd_offset = (p_nd_offset_before + p_nd_offset_after )/2
        else:
            p_nd_offset = p_nd_offset_before

        p_nd_ind = pres.get_value("nd_ind", "mbar")
        conv = const.get_conv(from_unit="mbar", to_unit=unit)
        p_nd = (p_nd_ind - p_nd_offset)*conv

        CustomerDevice = Cdg( doc, io.get_doc_db("cob-cdg-nd_se3"))
        u_p_nd = CustomerDevice.get_total_uncert(p_nd_ind, unit, unit, skip_type="A")

        res.store("Pressure", "nd_corr", p_nd, unit)
        res.store("Uncertainty", "nd_corr", u_p_nd, unit)

        ## -------------------------
        # Unsicherheit Ausgasung:
        ## -------------------------
        p_rise_rate = 3e-8 #Pa/s gemessen: 2019-01-18 08:40:27 (s. state docs)
        t = time.get_rmt("amt_meas", "ms")
        conv = const.get_conv(from_unit="ms",to_unit="s")
        p_rise = p_rise_rate * t * conv
        u_p_rise = 0.2 # Druckanstieg 20% Unsicher
        
        res.store("Pressure", "rise", p_rise , unit)
        res.store("Uncertainty", "rise", p_rise*u_p_rise/p_1 , "1")

        ## -------------------------
        # f:
        ## -------------------------
        p_a = p_1 - p_nd + p_rise
        p_b = p_0 * rg * dh
        n = len(p_a)
        x = np.full(n, 0.0)
        y = np.full(n, 0.0)
        for i in range(n):
            # y[i] = p_a[i]/p_b[i]*T_0[i]/T_1[i] ## okish
            if i == 0:
                
                y[i] = p_a[i]
                x[i] = p_b[i]*T_0[i]/T_1[i]
            else:
                #x[i] = p_a[i - 1]/T_1[i -1]*T_0[i]/p_0[i] ## okish
                y[i] = p_a[i] - p_a[i-1]*T_1[i]/T_1[i-1]
                x[i] = p_b[i]*T_1[i]/T_0[i] - p_a[i-1]*T_1[i]/T_1[i-1]

        f = y/x
        f = np.delete(f, f.argmin())
        f = np.delete(f, f.argmax())
        print(np.mean(f))
        print(np.std(f)/np.mean(f))

        
        doc = res.build_doc()
                
        io.save_doc(doc)
        io.save_doc(res.build_doc())


if __name__ == "__main__":
    main()
