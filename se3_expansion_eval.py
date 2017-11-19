import sys
import numpy as np
from vpy.vpy_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal as FrsCalc
from vpy.standard.frs5.uncert import Uncert as FrsUncert
from vpy.standard.se3.cal import Cal as Se3Calc
#from vpy.standard.se3.uncert import Uncert as FrsUncert

if __name__ == "__main__":

    io = Io()
    log = io.logger(__name__)
    log.info("start logging")

    doc = io.load_doc()
    if doc:
        res        = Analysis(doc)

        se3_calc   =  Se3Calc(doc)

        frs_calc   = FrsCalc(doc)
        frs_uncert = FrsUncert(doc)

        frs_calc.temperature(res)
        frs_calc.pressure_res(res)
        frs_calc.pressure_cal(res)

        #frs_uncert.total(res)

        se3_calc.temperature_before(res)
        se3_calc.temperature_after(res)
        se3_calc.temperature_room(res)
        se3_calc.pressure_fill(res)
        se3_calc.pressure_nd(res)
        se3_calc.real_gas_correction(res)

        rg   = res.pick("Correction", "rg", "1")
        p_0  = res.pick("Pressure", "fill", "mbar")
        p_1  = res.pick("Pressure", "frs5", "mbar")
        p_nd = res.pick("Pressure", "nd", "mbar")
        T_0  = res.pick("Temperature", "before", "K")
        T_1  = res.pick("Temperature", "after", "K")

        cor_tem  =  T_0 / T_1
        f        = (p_1 - p_nd)/(p_0 * rg) * cor_tem

        res.store("Correction", "temperature_expansion", cor_tem, "1")
        #res.store("Expansion", se3.get_expansion()[-1], f, "1")
        log.info("expansin factors are: {}".format(f))
        #log.info("standard deviation of mean value: {}".format(np.nanstd(f)/np.nanmean(f)/np.sqrt(len(f))))
        io.save_doc(res.build_doc())
