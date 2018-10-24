"""
python se3_cal_analysis.py --ids 'cal-2018-se3-ik-4825_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
from vpy.standard.se3.uncert import Uncert

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split(';')
        except:
           fail = True
    if '--update' in args:
        update = True
    else:
        update = False

    base_doc = io.get_base_doc("se3")
    
    if not fail and len(ids) >0:
        for id in ids:
            if update:
                meas_doc = io.get_doc_db(id)
                doc = io.update_cal_doc(meas_doc, base_doc)
                cal = Cal(doc)
            else:
                doc = io.get_doc_db(id)
                cal = Cal(doc)

            res = Analysis(doc)
        
            state_doc = io.get_state_doc("se3", meas_date=cal.Date.first_measurement()) 
            cal.insert_state_results(res, state_doc)
            
            cal.pressure_fill(res)
            cal.deviation_target_fill(res)
            cal.temperature_before(res)
            cal.temperature_after(res)
            cal.temperature_room(res)
            cal.real_gas_correction(res)
            cal.volume_add(res)
            cal.volume_start(res)
            cal.expansion(res)
            cal.pressure_rise(res)

            cal.pressure_cal(res)
            cal.error_pressure_rise(res)
            
            cal.pressure_ind(res)
            cal.deviation_target_cal(res)
            cal.error(res)

            io.save_doc(res.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))        

if __name__ == "__main__":
    main()
