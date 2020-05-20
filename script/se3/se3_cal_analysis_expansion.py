"""
python script/se3/se3_cal_analysis_expansion.py --ids 'cal-2019-se3-kk-75002_0001'  # -a #--> new aux values
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
from vpy.standard.se3.uncert import Uncert
from vpy.device.cdg import InfCdg, Cdg
from vpy.device.srg import Srg
from vpy.device.rsg import Rsg


def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids]
            ids = ids.split('@')
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

    cmc = False
    
    if not fail and len(ids) > 0:
        base_doc = io.get_base_doc("se3")
        for id in ids:
            id = id.replace("\"", "")

            doc = io.get_doc_db(id)
            if update:
                doc = io.update_cal_doc(doc, base_doc)

            if auxval: ## get new the AuxValues from related (meas_date) state measurement 
                cal = Cal(doc)
                meas_date = cal.Date.first_measurement()
                state_doc = io.get_state_doc("se3", date=meas_date) 
                res = Analysis(doc, analysis_type="expansion")
                cal.insert_state_results(res, state_doc)
            else: ## keep AuxValues from Calibration.Analysis.AuxValues
                auxvalues = doc.get('Calibration').get('Analysis', {}).get('AuxValues', {})
                res = Analysis(doc, insert_dict={'AuxValues': auxvalues}, analysis_type="expansion")
                cal = Cal(doc)
            
            if 'CustomerObject' in doc['Calibration']:
                customer_device = doc['Calibration']['CustomerObject']
                dev_class = customer_device.get('Class', "generic")
                if dev_class == 'SRG':
                   cus_dev = Srg(doc, customer_device)
                if dev_class == 'CDG':
                   cus_dev = Cdg(doc, customer_device)
                if dev_class == 'RSG':
                   cus_dev = Rsg(doc, {})
            #cal.pressure_fill(res)
            cal.pressure_gn_corr(res)
            cal.pressure_gn_mean(res)
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
            cal.correction_delta_height(res)
            cal.pressure_cal(res)
            cal.error_pressure_rise(res)
            cal.deviation_target_cal(res)
            
            ## uncert. calculation
            uncert = Uncert(doc)
            if cmc:
                # bis update CMC Einträge --> vorh. CMC Einträge  
                # cal uncertainty of standard
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
            else:
                uncert.cmc(res)    

            ## calculate customer indication
            gas = cal.Aux.get_gas()
            temperature_dict = res.pick_dict('Temperature', 'after')
            offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )    
            ind_dict = cal.Pres.get_dict('Type', 'ind' )
            range_dict = cal.Range.get_dict('Type', 'ind' )

            offset = cus_dev.pressure(offset_dict, temperature_dict, range_dict=range_dict, unit = cal.unit, gas=gas)
            ind = cus_dev.pressure(ind_dict, temperature_dict, range_dict=range_dict, unit = cal.unit, gas=gas)
            
            res.store("Pressure", "offset", offset, cal.unit)
            res.store("Pressure", "ind", ind, cal.unit)
            res.store("Pressure", "ind_corr", ind - offset, cal.unit)
            
            # error for rating procedures
            ind = res.pick("Pressure", "ind_corr", cal.unit)
            cal = res.pick("Pressure", "cal" , cal.unit)        
            res.store('Error', 'ind', ind/cal-1, '1')
            
            cus_dev.range_trans(res)
            
            io.save_doc(res.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))
if __name__ == "__main__":
    main()
