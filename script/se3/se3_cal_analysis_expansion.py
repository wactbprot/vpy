"""
python script/se3/se3_cal_analysis_expansion.py --ids 'cal-2019-se3-kk-75002_0001'  -a # keep aux values
"""
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal

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
                res = Analysis(doc, insert_dict={'AuxValues': auxvalues}, analysis_type="expansion")
                cal = Cal(doc)
            else:
                # renew the AuxValues
                cal = Cal(doc)
                meas_date = cal.Date.first_measurement()
                state_doc = io.get_state_doc("se3", date=meas_date) 
                res = Analysis(doc, analysis_type="expansion")
                cal.insert_state_results(res, state_doc)
              
            cal.pressure_fill(res)
            cal.deviation_target_fill(res)
            cal.temperature_before(res)
            cal.temperature_after(res)
            cal.temperature_room(res)
            cal.temperature_gas_expansion(res)
            cal.real_gas_correction(res)
            cal.volume_add(res)
            cal.volume_start(res)
            cal.expansion(res)
            cal.pressure_rise(res)
            cal.range(res)
            cal.pressure_cal(res)
            cal.pressure_ind(res)
            cal.error(res)
            cal.error_pressure_rise(res)
            cal.deviation_target_cal(res)
            io.save_doc(res.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))        

if __name__ == "__main__":
    main()
