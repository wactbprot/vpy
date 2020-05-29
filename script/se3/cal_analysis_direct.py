"""
python script/se3/cal_analysis_direct.py --ids 'cal-2019-se3-ik-4625_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
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
from vpy.helper import init_customer_device

def main():
    io = Io()
    io.eval_args()
    ret = {'ok':True}

    ids = io.parse_ids_arg()
    update = io.parse_update_arg()
    cmc = False

    base_doc = io.get_base_doc("se3")
    for id in ids:
        doc = io.get_doc_db(id)
        if update:
            doc = io.update_cal_doc(doc, base_doc)

        cal = Cal(doc)
        ana = Analysis(doc, analysis_type="direct")

        cus_dev = init_customer_device(doc)
    
        cus_dev.range_trans(ana)
        cal.temperature_comp(ana)
        cal.temperature_gas_direct(ana)
        cal.pressure_gn_corr(ana)
        cal.pressure_gn_mean(ana)
        
        temperature_dict = ana.pick_dict('Temperature', 'compare')
        gas = cal.Aux.get_gas()
        ind_dict = cal.Pres.get_dict('Type', 'ind' )
        offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )
        range_dict = cal.Range.get_dict('Type', 'ind' )
        
        ind = cus_dev.pressure(ind_dict, temperature_dict, range_dict=range_dict, unit=ana.pressure_unit, gas=gas)
        offset = cus_dev.pressure(offset_dict, temperature_dict, range_dict=range_dict, unit=ana.pressure_unit, gas=gas)
            
        ana.store("Pressure", "ind", ind, ana.pressure_unit)
        ana.store("Pressure", "offset", offset, ana.pressure_unit)
        ana.store("Pressure", "ind_corr", ind - offset, ana.pressure_unit)
            
        # error for rating procedures
        p_ind = ana.pick("Pressure", "ind_corr", cal.unit)
        p_cal = ana.pick("Pressure", "cal" , cal.unit)
        ana.store('Error', 'ind', p_ind/p_cal-1.0, '1')
        
        ## uncert. calculation
        uncert = Uncert(doc)
        
        ## we have cmc entries for the FRS
        ## so we can use the GN uncertainty
        u = uncert.contrib_pressure_fill(p_cal, cal.unit)
        ana.store("Uncertainty", "standard", u/p_cal, "1")

        io.save_doc(ana.build_doc())
    
    print(json.dumps(ret))

if __name__ == "__main__":
    main()
