"""
python script/se3/se3_cal_analysis.py --ids 'cal-2018-se3-ik-4825_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.std import Se3

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

    if '-u' in args:
        update = True
    else:
        update = False
    
    if '-a' in args:
        auxval = True
    else:
        auxval = False

    if not fail and len(ids) >0:
        base_doc = io.get_base_doc("se3")
        for id in ids:
            doc = io.get_doc_db(id)
            if update:
                doc = io.update_cal_doc(doc, base_doc)

            if auxval: ## keep auxvalues
                # keep the AuxValues containing related outgasing and additional volumes
                auxvalues = doc.get('Calibration').get('Analysis', {}).get('AuxValues', {})
                res = Analysis(doc, insert_dict={'AuxValues': auxvalues})
                cal = Cal(doc)
            else:
                 # renew the AuxValues
                cal = Cal(doc)
                meas_date = cal.Date.first_measurement()
                state_doc = io.get_state_doc("se3", date=meas_date) 
                res = Analysis(doc)
                cal.insert_state_results(res, state_doc)
            
            uncert = Uncert(doc)            
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

            uncert.define_model()
            uncert.gen_val_dict(res)
            uncert.gen_val_array(res)
            uncert.volume_start(res)
            uncert.volume_5(res)
            uncert.pressure_fill(res)
            uncert.temperature_after(res)
            uncert.temperature_before(res)
            uncert.expansion(res)
            uncert.total(res)
            
            io.save_doc(res.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))        

if __name__ == "__main__":
    main()
