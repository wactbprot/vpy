"""
python se3_calibration.py --id 'cal-2018-se3-ik-4925_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
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
    state_doc = io.get_state_doc("se3") 
    res = Analysis(doc)
 
    cal = Cal(doc)
    cal.insert_state_results(res, state_doc)
    cal.pressure_fill(res)
    cal.temperature_before(res)
    cal.temperature_after(res)
    cal.real_gas_correction(res)
    cal.volume_add(res)
    cal.volume_start(res)
    cal.expansion(res)
    
    cal.pressure_cal(res)

    cal.pressure_ind(res)
    p_ind = res.pick('Pressure', 'ind_corr', 'Pa')
    p_cal = res.pick('Pressure', 'cal', 'Pa')
    print(p_ind/p_cal)
    io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
