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
 
    ## get Volumes and outgasing from latest state document
    state_doc = io.get_state_doc("se3") 
    ok = [state_doc is not None,
             'State' in state_doc,
             'Measurement' in state_doc['State'],
             'Date' in state_doc['State']['Measurement'],
             isinstance(state_doc['State']['Measurement']['Date'], list),
             isinstance(doc['Calibration']['Measurement']['Date'], list),
             'Analysis' in state_doc['State'],
             'Values' in state_doc['State']['Analysis'],
             'Volume' in state_doc['State']['Analysis']['Values'], 
             'Time' in state_doc['State']['Analysis']['Values'],
             'OutGasRate' in state_doc['State']['Analysis']['Values'],
             ]     

    if all(ok):    
        volumes = state_doc['State']['Analysis']['Values']['Volume']
        outgasrates = state_doc['State']['Analysis']['Values']['OutGasRate']
        times = state_doc['State']['Analysis']['Values']['Time']
    else:
        sys.exit('missing state or wrong structure')

    res = Analysis(doc)
    for volume in volumes:
        res.store_dict('Volume', volume, dest="AuxValues")
    for outgasrate in outgasrates:
        res.store_dict('OutGasRate', outgasrate, dest="AuxValues")
    for time in times:
        res.store_dict('Time', time, dest="AuxValues")
    cal = Cal(doc)
    cal.pressure_cal(res)
    
    io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
