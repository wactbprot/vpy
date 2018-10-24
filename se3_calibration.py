"""
python se3_calibration.py --id 'cal-2018-se3-ik-4825_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
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
    doc = io.load_doc() 
    # keep the AuxValues containing related Outgasing and additional volumes
    auxvalues = doc.get('Calibration').get('Analysis', {}).get('AuxValues', {})
    res = Analysis(doc, insert_dict={'AuxValues':auxvalues})

    cal = Cal(doc)
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
