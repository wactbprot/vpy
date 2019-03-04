"""
python script/se3/se3_cal_analysis_direct.py --ids 'cal-2019-se3-ik-4625_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
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
    unit = "Pa"

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

            cal.temperature_comp(res)           
            cal.pressure_comp(res)
            
            cal.offset_from_sample(res)

            gas = cal.Aux.get_gas()

            temperature_dict = res.pick_dict('Temperature', 'compare')
            
           
            ind_dict = cal.Pres.get_dict('Type', 'ind' )
            offset = res.pick("Pressure","offset_sample", unit)
            ind = cal.CustomerDevice.pressure(ind_dict, temperature_dict, unit=unit, gas=gas)
             
            res.store("Pressure", "ind", ind, unit)
            res.store("Pressure", "ind_corr", ind - offset, unit)

            cal.error(res)
            
            io.save_doc(res.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))        

if __name__ == "__main__":
    main()
