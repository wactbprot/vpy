"""
python se3_calibration.py --id 'cal-2018-se3-ik-4925_0001' --db 'vl_db' --srv 'http://localhost:5984'
"""
import sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
from vpy.standard.se3.uncert import Uncert

def main():
    io = Io()
    io.eval_args()
    meas_doc = io.load_doc()
    base_doc = io.get_base_doc("se3")
    doc = io.update_cal_doc(meas_doc, base_doc)
    res = Analysis(doc)

    cal = Cal(doc)
    cal.pressure_cal(res)

if __name__ == "__main__":
    main()
