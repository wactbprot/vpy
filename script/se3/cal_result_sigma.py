"""
python script/se3/cal_result_sigma.py --ids 'cal-2018-se3-kk-75050_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import os
sys.path.append(".")

import copy
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result

from vpy.values import Values
from vpy.analysis import Analysis
from vpy.constants import Constants 

from vpy.display.se3 import SE3 as Display
from vpy.helper import init_customer_device, result_analysis_init

def main():
    io = Io()
    io.eval_args()
    ret = {'ok':True}

    cmc = False

    ids = io.parse_ids_arg()
    skip = io.parse_skip_arg()
        
    for id in ids:
        doc = io.get_doc_db(id)
        display = Display(doc)
        
        cus_dev = init_customer_device(doc)
        ana = result_analysis_init(doc)
        
        ## generate result instance with analysis res type
        
        res = Result(doc, result_type=ana.analysis_type, skip=skip)
        if res.ToDo.type != "sigma":
            sys.exit("wrong script")
        
        p_cal = ana.pick('Pressure', 'cal', ana.pressure_unit)
        p_ind_corr = ana.pick('Pressure', 'ind_corr', ana.pressure_unit)
        
        ## will be filled up with aux values:
        d = {}
        
        sigma = ana.pick("Sigma", "eff", "1") 
        if sigma is None:
            sigma = p_ind_corr/p_cal
            ana.store("Sigma", "eff", sigma, "1")
        
        display.check_sigma(ana)
        
        all_index = cus_dev.make_sigma_index(p_cal, ana.pressure_unit)
        average_index, reject_index  = ana.ask_for_reject(average_index=all_index)
        flat_average_index = ana.flatten(average_index)            
        d["AverageIndex"] = average_index
        d["AverageIndexFlat"] = flat_average_index
        ana.store_dict(quant='AuxValues', d=d, dest=None)
    
        ## reduce 
        p_cal = np.take(p_cal, flat_average_index)
        p_ind = np.take(p_ind_corr, flat_average_index)
        sigma = np.take(sigma, flat_average_index)
    
        ## store reduced quant. for plot
        ana.store("Pressure", "red_ind_corr", p_ind, ana.pressure_unit, dest="AuxValues")
        ana.store("Pressure", "red_cal", p_cal, ana.pressure_unit, dest="AuxValues")
        ana.store("Sigma", "red_eff", sigma, "1", dest="AuxValues")
        
        ## cal. sigma
        sigma_null, sigma_slope, sigma_std = cus_dev.sigma_null(p_cal, ana.pressure_unit, p_ind, ana.pressure_unit)
        d["SigmaNull"] = float(sigma_null)
        d["SigmaSlope"] = float(sigma_slope)
        d["SigmaCorrSlope"] = float(np.abs(sigma_slope/sigma_null))
        d["SigmaStd"] = float(sigma_std)
        ana.store_dict(quant='AuxValues', d=d, dest=None)

        ## cal. offset and offset scatter
        aux_values_pres = Values(doc.get('Calibration').get('Measurement').get("AuxValues").get("Pressure"))
        rd, rd_unit = aux_values_pres.get_value_and_unit(d_type="offset")
        d["OffsetMean"] = float(np.nanmean(rd))
        d["OffsetStd"] = float(np.nanstd(rd))
        d["OffsetUnit"] = rd_unit
        res.store_dict(quant='AuxValues', d=d, dest=None)
        
        ## uncert contribs.
        cus_dev.uncert_sigma_eff(ana)
        cus_dev.uncert_ind(ana)
        cus_dev.uncert_temperature(ana)
        cus_dev.uncert_offset(ana)
        cus_dev.uncert_repeat(ana)
        cus_dev.device_uncert(ana) 
            
        ## the uncertainty of the standard is 
        # already calculated at analysis step            
        ana.total_uncert()
        
        u_tot = ana.pick("Uncertainty", "total_rel", "1")
        ana.store("Uncertainty", "red_u_tot", np.take(u_tot, flat_average_index), "1", dest="AuxValues")
        
        # start making data sections
        res.make_measurement_data_section(ana, result_type=ana.analysis_type)
        
        display.plot_sigma(ana)
        
        doc = ana.build_doc("Analysis", doc)
        doc = res.build_doc("Result", doc)
        io.save_doc(doc)
        
if __name__ == "__main__":
    main()
