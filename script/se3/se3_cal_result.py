"""
python script/se3/se3_cal_result.py --ids 'cal-2018-se3-kk-75050_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import os
sys.path.append(".")

import copy
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.todo import ToDo
from vpy.values import Values
from vpy.analysis import Analysis
from vpy.constants import Constants 
from vpy.device.srg import Srg
from vpy.device.cdg import Cdg
from vpy.device.rsg import Rsg
from vpy.display.se3 import SE3 as Display
import matplotlib.pyplot as plt

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}
    unit = 'Pa'
    cmc = False

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split('@')
        except:
           fail = True

    if '--skip' in args:
        skip = True
    else:
        skip = False

    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
            display = Display(doc)
            
            customer_object = doc.get('Calibration').get('CustomerObject')
            if customer_object.get("Class") == "SRG":
                cus_dev = Srg(doc, customer_object)
            if customer_object.get("Class") == "CDG":
                cus_dev = Cdg(doc, customer_object)
            if customer_object.get("Class") == "RSG":
                cus_dev = Rsg(doc, customer_object)   
            
            analysis = doc.get('Calibration').get('Analysis')
            
            ## keep standard uncertainty and clean the rest
            u_std = Values(analysis.get("Values").get("Uncertainty")).get_value("standard", "1")
            del analysis['Values']['Uncertainty']
            ana = Analysis(doc, init_dict=analysis)
            ana.store("Uncertainty", "standard", u_std, "1")

            ## generate result instance with analysis res type
            result_type = analysis.get("AnalysisType", "default")
            res = Result(doc, result_type=result_type, skip=skip)

            p_cal_dict = ana.pick_dict('Pressure', 'cal')
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)

            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)

            ## will be filled up with aux values:
            d = {} 
            if res.ToDo.type == "error":
                err = ana.pick("Error", "ind", "1") 

                display.check_p_e(p_cal, err)
                average_index, reject_index  = ana.ask_for_reject(average_index=average_index)
                flat_average_index = ana.flatten(average_index)
            
                ## rm values
                p_cal = np.take(p_cal, flat_average_index)
                p_ind_corr = np.take(p_ind_corr, flat_average_index)
                err = np.take(err, flat_average_index)
                
                # get from customer object
                temperature_head, head_unit = ana.ask_for_head_temperature(temperature_head=45.0) 
                if temperature_head:
                    ## e_vis fit
                    params = cus_dev.get_e_vis_fit_params(np.delete(p_cal, reject_index), np.delete(err, reject_index)*100)

                    ## plot model
                    display.check_p_e(p_cal, err, label="measurement", show=False)
                    err_model = cus_dev.e_vis_model(p_cal, *params)/100.
                    e_vis_cal = cus_dev.e_vis_model(100., *params)/100.
                    display.e_vis_line(e_vis_cal)
                    display.check_p_e(p_cal, err_model, label="model")                    

                    ## find e_vis
                    t_head = temperature_head + res.Const.get_conv(from_unit=head_unit, to_unit="K")
                    t_head_dict = {"Value":t_head, "Unit":"K"}
                    tdo_unit = res.ToDo.temperature_unit
                    t_target = res.ToDo.Temp.get_value("target", tdo_unit) + res.Const.get_conv(from_unit=tdo_unit, to_unit="K")
                    t_norm_dict = {"Value":t_target, "Unit":"K"}

                    t_gas_dict = ana.pick_dict("Temperature", "after")
                    e_dict = ana.pick_dict("Error", "ind")
                    
                    e_vis, cf_vis, u_vis, vis_unit = ana.ask_for_evis(e_vis_cal)

                    d["AverageIndex"] = average_index
                    d["AverageIndexFlat"] = flat_average_index
                    d["Evis"] = e_vis
                    d["CFvis"] = cf_vis
                    d["Uvis"] = u_vis
                    d["VisUnit"] = vis_unit
                    ## float() avoids that the value becomes an array
                    d["TemperatureHead"] = float(t_head[0])
                    d["TemperatureHeadUnit"] = "K"
                    d["TemperatureNorm"] = float(t_target[0])
                    d["TemperatureNormUnit"] = "K"
                    
                    err_norm = cus_dev.temperature_correction(e_dict, p_cal_dict, t_gas_dict, t_head_dict, t_norm_dict, e_vis, vis_unit)
                    ana.store("Error", "ind_temperature_corr",  err_norm, e_dict.get("Unit"))
                    err_norm = np.take(err_norm,  flat_average_index)
                    
                    display.plot_p_ediff(p_cal, err_norm - err)

                    ## offset contrib
                    cus_dev.offset_uncert(ana, use_idx = flat_average_index)
                        
            if res.ToDo.type == "sigma":
                sigma = ana.pick("Sigma", "eff", "1") 
                if sigma is None:
                    sigma = p_ind_corr/p_cal
                    
                display.check_p_sigma(p_ind_corr, sigma)
                skip = ana.ask_for_skip()

                p_cal = np.delete(p_cal, skip)
                p_ind = np.delete(p_ind_corr, skip)
                
                sigma_null, sigma_slope, sigma_std = cus_dev.sigma_null(p_cal=p_cal,
                                                                        cal_unit=unit,
                                                                        p_ind=p_ind,
                                                                        ind_unit=unit)

                aux_values_pres = Values(doc.get('Calibration').get('Measurement').get("AuxValues").get("Pressure"))
                rd, rd_unit = aux_values_pres.get_value_and_unit(d_type="offset")
                d["SkipIndex"] = skip
                d["SigmaNull"] = sigma_null
                d["SigmaCorrSlope"] = np.abs(sigma_slope/sigma_null)
                d["SigmaStd"] = sigma_std
                d["OffsetMean"] = np.nanmean(rd)
                d["OffsetStd"] = np.nanstd(rd)
                d["OffsetUnit"] = rd_unit

                ## offset contrib
                cus_dev.offset_uncert(ana)
                
            ## write d to res without `plain=True`
            ## in order to keep githash info           
            res.store_dict(quant='AuxValues', d=d, dest=None)

            ## default uncert. contrib.
            cus_dev.repeat_uncert(ana)
            cus_dev.device_uncert(ana) 
            if "Uncertainty" in customer_object:
                ## e.g. for digitalisation uncert.
                u_dev = cus_dev.get_total_uncert(meas_vec=p_ind_corr,
                                                 meas_unit="Pa",
                                                 return_unit="Pa",
                                                 res=ana,
                                                 skip_source="standard",
                                                prefix=False)
            ## the uncertainty of the standard is 
            # already calculated at analysis step            
            ana.total_uncert() 
   
            # start making data sections
            res.make_measurement_data_section(ana, result_type=result_type)

            if res.ToDo.type == "error":
                # start build cert table
                p_ind_mv, err_mv, u_mv =res.make_error_table(ana, pressure_unit=unit, error_unit='1')
                display.plot_p_e_u(p_ind_mv, err_mv, u_mv, show=False)
                display.check_p_e(p_ind_corr, err)
                        
            if res.ToDo.type == "sigma":
                display.check_p_sigma(p_ind_corr, sigma, show=False)
                display.check_p_sigma(p_ind_corr, sigma_slope * p_cal + sigma_null, label="fit")
                    
            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
