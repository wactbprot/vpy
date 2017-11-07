import sys
import numpy as np
from vpy.vpy_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5 import Frs5
from vpy.standard.se3  import Se3
from vpy.log import log

if __name__ == "__main__":

    log = log().getLogger(__name__)
    io = Io()
    log.info("start logging")

    doc = io.load_doc()
    if doc:
        res  = Analysis(doc)
        se3  = Se3(doc)

        frs5 = Frs5(doc)
        frs5.temperature(res)
        frs5.pressure_res(res)
        frs5.pressure_cal(res)
        frs5.uncertainty(res)

        se3.temperature_before(res)
        se3.temperature_after(res)
        se3.pressure_fill(res)
        se3.pressure_nd(res)
        se3.real_gas_correction(res)

        rg   = res.pick("Correction", "rg", "1")
        p_0  = res.pick("Pressure", "fill", "mbar")
        p_1  = res.pick("Pressure", "frs5", "mbar")
        p_nd = res.pick("Pressure", "nd", "mbar")
        T_0  = res.pick("Temperature", "before", "K")
        T_1  = res.pick("Temperature", "after", "K")

        cor_tem  =  T_0 / T_1
        f_m  = (p_1 - p_nd)/(p_0 * rg) * cor_tem

        res.store("Correction", "temperature_expansion", cor_tem, "1")
        res.store("Expansion", "m", f_m, "1")
        print(f_m)
        print(np.std(f_m)/np.mean(f_m)/np.sqrt(len(f_m)))
        io.save_doc(res.build_doc())
