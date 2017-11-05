from log import log
import sys
from vpy_io import Io
from analysis import Analysis
from standard.frs5 import Frs5
from standard.se3  import Se3

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

        io.save_doc(res.build_doc())
