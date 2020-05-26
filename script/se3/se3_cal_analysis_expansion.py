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
from vpy.todo import ToDo
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

    cmc = True
    
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
                ana = Analysis(doc, analysis_type="expansion")
                cal.insert_state_results(ana, state_doc)
            else: ## keep AuxValues from Calibration.Analysis.AuxValues
                auxvalues = doc.get('Calibration').get('Analysis', {}).get('AuxValues', {})
                ana = Analysis(doc, insert_dict={'AuxValues': auxvalues}, analysis_type="expansion")
                cal = Cal(doc)
            
            if 'CustomerObject' in doc.get('Calibration'):
                customer_device = doc.get('Calibration').get('CustomerObject')
                dev_class = customer_device.get('Class', "generic")
                if dev_class == 'SRG':
                   cus_dev = Srg(doc, customer_device)
                if dev_class == 'CDG':
                   cus_dev = Cdg(doc, customer_device)
                if dev_class == 'RSG':
                   cus_dev = Rsg(doc, {})

            uncert = Uncert(doc)
            tdo = ToDo(doc)
             
            cal.pressure_gn_corr(ana)
            cal.pressure_gn_mean(ana)
            cal.deviation_target_fill(ana)
            cal.temperature_before(ana)
            cal.temperature_after(ana)
            cal.temperature_room(ana)
            cal.temperature_gas_expansion(ana)
            cal.real_gas_correction(ana)
            cal.volume_add(ana)
            cal.volume_start(ana)
            cal.expansion(ana)
            cal.pressure_rise(ana)
            cal.correction_delta_height(ana)
            cal.pressure_cal(ana)
            cal.error_pressure_rise(ana)
            cal.deviation_target_cal(ana)
            
            ## uncert. calculation
            
            if cmc:
                # bis update CMC Einträge --> vorh. CMC Einträge  
                # cal uncertainty of standard
                uncert.cmc(ana)
            else:            
                uncert.define_model()
                uncert.gen_val_dict(ana)
                uncert.gen_val_array(ana)
                uncert.volume_start(ana)
                uncert.volume_5(ana)
                uncert.pressure_fill(ana)
                uncert.temperature_after(ana)
                uncert.temperature_before(ana)
                uncert.expansion(ana)
                uncert.total(ana)

            ## calculate customer indication
            gas = cal.Aux.get_gas()
            temperature_dict = ana.pick_dict('Temperature', 'after')
            offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )    
            ind_dict = cal.Pres.get_dict('Type', 'ind' )
            range_dict = cal.Range.get_dict('Type', 'ind' )

            offset = cus_dev.pressure(offset_dict, temperature_dict, range_dict=range_dict, unit = cal.unit, gas=gas)
            ind = cus_dev.pressure(ind_dict, temperature_dict, range_dict=range_dict, unit = cal.unit, gas=gas)
            
            ana.store("Pressure", "offset", offset, cal.unit)
            ana.store("Pressure", "ind", ind, cal.unit)
            ana.store("Pressure", "ind_corr", ind - offset, cal.unit)
            
            ind = ana.pick("Pressure", "ind_corr", cal.unit)
            cal = ana.pick("Pressure", "cal" , cal.unit)        

            if tdo.type == "error":
                print(ind/cal-1)
                ana.store('Error', 'ind', ind/cal-1, '1')
                cus_dev.range_trans(ana)
                
            if tdo.type == "sigma":
                ana.store('Sigma', 'eff', ind/cal, '1')

            io.save_doc(ana.build_doc())           
    else:
        ret = {"error": "no --ids found"}
    
    print(json.dumps(ret))
if __name__ == "__main__":
    main()
