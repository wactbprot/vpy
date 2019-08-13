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

from vpy.device.cdg import InfCdg, Cdg
from vpy.device.srg import Srg
from vpy.device.rsg import Rsg

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
            ids = args[idx_ids].split('@')
        except:
           fail = True

    if '-u' in args:
        update = True
    else:
        update = False
    

    if not fail and len(ids) >0:
        base_doc = io.get_base_doc("se3")
        for id in ids:
            doc = io.get_doc_db(id)
            if update:
                doc = io.update_cal_doc(doc, base_doc)

            # renew the AuxValues
            cal = Cal(doc)
            res = Analysis(doc, analysis_type="direct")

            if 'CustomerObject' in doc['Calibration']:
                customer_device = doc['Calibration']['CustomerObject']
                dev_class = customer_device.get('Class', "generic")
                if dev_class == 'SRG':
                    CustomerDevice = Srg(doc, customer_device)
                if dev_class == 'CDG':
                    CustomerDevice = Cdg(doc, customer_device)
                if dev_class == 'RSG':
                    CustomerDevice = Rsg(doc, {})
      
            cal.temperature_comp(res)
            cal.temperature_gas_direct(res)
            cal.pressure_gn_corr(res)
            cal.pressure_gn_mean(res)
            
            
            ## !!cal.offset_from_sample(res)
            ## !!offset_dict = res.pick_dict("Pressure","offset_sample")

            temperature_dict = res.pick_dict('Temperature', 'compare')
            gas = cal.Aux.get_gas()
            ind_dict = cal.Pres.get_dict('Type', 'ind' )
            offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )
            ind = CustomerDevice.pressure(ind_dict, temperature_dict, unit=unit, gas=gas)
            offset = CustomerDevice.pressure(offset_dict, temperature_dict, unit=unit, gas=gas)
            
            res.store("Pressure", "ind", ind, unit)
            res.store("Pressure", "ind_corr", ind - offset, unit)
            
            # error for rating procedures
            ind = res.pick("Pressure", "ind_corr", cal.unit)
            cal = res.pick("Pressure", "cal" , cal.unit)
            res.store('Error', 'ind', ind/cal-1.0, '1')
            
            io.save_doc(res.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))

if __name__ == "__main__":
    main()
