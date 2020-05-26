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
            
            customer_object = doc.get('Calibration').get('CustomerObject')
            if customer_object.get("Class") == "SRG":
                cus_dev = Srg(doc, customer_object)
            if customer_object.get("Class") == "CDG":
                cus_dev = Cdg(doc, customer_object)
            if customer_object.get("Class") == "RSG":
                cus_dev = Rsg(doc, customer_object)   
            tdo = ToDo(doc)

            analysis = doc.get('Calibration').get('Analysis')
            ## keep standard uncertainty and clean the rest

            u_std = Values(analysis.get("Values").get("Uncertainty")).get_value("standard", "1")
            del analysis['Values']['Uncertainty']

            ana = Analysis(doc, init_dict=analysis)
            ## keep uncert of standard only
            ana.store("Uncertainty", "standard", u_std, "1")
            
            
            result_type = analysis.get("AnalysisType", "default")
            res = Result(doc, result_type=result_type, skip=skip)

            p_cal_dict = ana.pick_dict('Pressure', 'cal')
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)
            p_ind = ana.pick('Pressure', 'ind', unit)

            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)

            # plot to rm outliers and check
            if tdo.type == "error":
                err = ana.pick("Error", "ind", "1") 
                x = p_ind_corr
                y = err

            if tdo.type == "sigma":
                sigma = ana.pick("Sigma", "eff", "1") 
                x = p_ind_corr
                y = sigma
            
            if result_type == "direct" and tdo.type == "error":
                plt.xscale('symlog', linthreshx=1e-12)
                plt.plot(x, y, marker='o', linestyle="None", markersize=10, label="measurement")
                for i, v in enumerate(x):
                    plt.text(v, y[i], i, rotation=45.)
                plt.grid()
                plt.show()
            
                average_index, _ = ana.ask_for_reject(average_index=average_index)
                d = {"AverageIndex": average_index}
                
            if result_type == "expansion" and tdo.type == "error":
                plt.xscale('symlog', linthreshx=1e-12)
                plt.plot(x, y, marker='o', linestyle="None", markersize=10, label="measurement")
                for i, v in enumerate(x):
                    plt.text(v, y[i], i, rotation=45.)
                plt.legend()
                plt.grid()
                plt.show()
                
                average_index, reject_index = ana.ask_for_reject(average_index=average_index)
                d = {"AverageIndex": average_index}            

                # get from customer object
                temperature_head, head_unit = ana.ask_for_head_temperature(temperature_head=45.0) 
                if temperature_head:
                    ## e_vis fit
                    params = cus_dev.get_e_vis_fit_params(np.delete(p_cal, reject_index), np.delete(err, reject_index)*100)
                    
                    plt.plot(x, y, marker='o', linestyle="None", markersize=10, label="measurement")
                    for i, v in enumerate(x):
                        plt.text(v, y[i], i, rotation=45.)
                    plt.semilogx(p_cal, cus_dev.e_vis_model(p_cal, *params)/100, '-', label="model")
                        
                        
                    e_vis_cal =  cus_dev.e_vis_model(100., *params)/100.
                    plt.axhline(y=e_vis_cal,label="e_vis = {}".format(round(e_vis_cal, 5)))
                    
                    plt.legend()
                    plt.grid()
                    plt.show()
                   
                    t_head = temperature_head + res.Const.get_conv(from_unit=head_unit, to_unit="K")
                    t_head_dict = {"Value":t_head, "Unit":"K"}

                    tdo_unit = tdo.temperature_unit
                    t_target = tdo.Temp.get_value("target", tdo_unit) + res.Const.get_conv(from_unit=tdo_unit, to_unit="K")
                    t_norm_dict = {"Value":t_target, "Unit":"K"}
                    
                    t_gas_dict = ana.pick_dict("Temperature", "after")
                    e_dict = ana.pick_dict("Error", "ind")
                   
                    e_vis, cf_vis, u_vis, vis_unit = ana.ask_for_evis(e_vis_cal)
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
                    
                    plt.plot(p_cal, err_norm - err, marker='o', linestyle="None", markersize=10, label="$e_{corr} - e$")
                    plt.legend()
                    plt.grid()
                    plt.show()
                
            if result_type == "expansion" and tdo.type == "sigma":

                plt.plot(x, y, marker='o', linestyle="None", markersize=10, label="measurement")
                for i, v in enumerate(x):
                    plt.text(v, y[i], i, rotation=45.)
                
                plt.legend()
                plt.grid()
                plt.show()
                
                skip = ana.ask_for_skip()
                d = {"SkipIndex":skip}
               
                sigma_null, sigma_slope, sigma_std = cus_dev.sigma_null(p_cal= np.delete(p_cal, skip),
                                                                                cal_unit=unit,
                                                                                p_ind=np.delete(p_ind_corr, skip),
                                                                                ind_unit=unit)
                d["SigmaNull"]  = sigma_null
                d["SigmaCorrSlope"] = np.abs(sigma_slope/sigma_null)
                d["SigmaStd"] = sigma_std
 
                aux_values_pres = Values(doc.get('Calibration').get('Measurement').get("AuxValues").get("Pressure"))
                rd, rd_unit = aux_values_pres.get_value_and_unit(d_type="offset")
                d["OffsetMean"] = np.nanmean(rd)
                d["OffsetStd"] = np.nanstd(rd)
                d["OffsetUnit"] = rd_unit

            ## write d to res without `plain=True`
            ## in order to keep githash info
           
            res.store_dict(quant='AuxValues', d=d, dest=None)
            
            ## default uncert. contrib.
            cus_dev.offset_uncert(ana, use_idx = ana.flatten(average_index))
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

            if tdo.type == "error":
                # start build cert table
                p_ind_mv, err_mv, u_mv =res.make_error_table(ana, pressure_unit=unit, error_unit='1')
            
                plt.subplot(111)
                plt.xscale('symlog', linthreshx=1e-12)
                
                plt.errorbar(p_ind_mv, err_mv,   yerr=u_mv,  marker='8', linestyle=":", markersize=10, label="certificate")
                plt.plot(x, y, marker='o', linestyle="None", markersize=10, label="measurement")
                plt.legend()
                plt.title('Calib. of {}@SE3'.format(customer_object.get('Name')))
                plt.ylabel('$e$')
                plt.grid(True)
                plt.show()
            
            if tdo.type == "sigma":
                def lin_reg(p):
                    return sigma_slope * p + sigma_null 
               
                plt.subplot(111)
                plt.plot(p_cal, p_ind_corr/p_cal,  marker='8', linestyle=":", markersize=10, label="certificate")
                if len(skip) > 0:
                   
                    plt.plot(p_cal[skip], p_ind_corr[skip]/p_cal[skip],  marker='D', linestyle=":", markersize=10, label="points skipped")
                
                plt.plot(p_cal, lin_reg(p_cal), linestyle="-", label="linear reg.")
                plt.legend()
                plt.title('Calib. of {}@SE3'.format(customer_object.get('Name')))
                plt.ylabel('$\sigma$')
                plt.xlabel('$p_{}$ in {}'.format("{cal}", unit))
                plt.grid(True)
                plt.show()
            
            
            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
