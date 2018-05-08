import sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se2.cal import Cal
from vpy.standard.se2.uncert import Uncert



def main():
    """
    Example call:
        python se2_calibration.py --id 'cal-2018-se2-kk-75016_0001' --log d
    """
    io = Io()
    doc = io.load_doc()

        res = Analysis(doc)
        cal = Calc(doc)

        cal.temperature_before(res)
        cal.temperature_after(res)
        cal.pressure_fill(res)
        cal.real_gas_correction(res)
        cal.time(res)

        io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
