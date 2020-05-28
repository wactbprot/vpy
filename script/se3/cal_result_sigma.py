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
            
            cus_dev = init_customer_device(doc)
            ana = result_analysis_init(doc)
         
            ## generate result instance with analysis res type

            res = Result(doc, result_type=ana.analysis_type, skip=skip)
            if res.ToDo.type != "sigma":
                sys.exit("wrong script")
                
            p_cal_dict = ana.pick_dict('Pressure', 'cal')
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)

            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)

            ## will be filled up with aux values:
            d = {} 
            sigma = ana.pick("Sigma", "eff", "1") 
            if sigma is None:
                sigma = p_ind_corr/p_cal
                ana.store("Sigma", "eff", sigma, "1")

            display.check_p_sigma(p_ind_corr, sigma)


            average_index, reject_index  = ana.ask_for_reject(average_index=average_index)
            flat_average_index = ana.flatten(average_index)            
            d["AverageIndex"] = average_index
            d["AverageIndexFlat"] = flat_average_index
            ana.store_dict(quant='AuxValues', d=d, dest=None)

            p_cal = np.take(p_cal, flat_average_index)
            p_ind = np.take(p_ind_corr, flat_average_index)
            sigma = np.take(sigma, flat_average_index)
                
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
            res.store_dict(quant='AuxValues', d=d, dest=None)
                
            ## offset contrib
            cus_dev.offset_uncert(ana)
                            
            ## default uncert. contrib.  repeat
            cus_dev.repeat_uncert(ana)
            
            ## default uncert. contrib.  device
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
            
            ## store red version for plot
            u_rep = ana.pick("Uncertainty", "repeat", "1")
            u_off = ana.pick("Uncertainty", "offset", "1")
            u_tot = ana.pick("Uncertainty", "total_rel", "1")
            u_dev = ana.pick("Uncertainty", "device", "1")
            u_std = ana.pick("Uncertainty", "standard", "1")
            ana.store("Uncertainty", "red_u_rep", np.take(u_rep, flat_average_index), "1", dest="AuxValues")
            ana.store("Uncertainty", "red_u_std", np.take(u_std, flat_average_index), "1", dest="AuxValues")
            ana.store("Uncertainty", "red_u_dev", np.take(u_dev, flat_average_index), "1", dest="AuxValues")
            ana.store("Uncertainty", "red_u_tot", np.take(u_tot, flat_average_index), "1", dest="AuxValues")
            ana.store("Uncertainty", "red_u_off", np.take(u_off, flat_average_index), "1", dest="AuxValues")

            display.plot_uncert(ana)
            
            # start making data sections
            res.make_measurement_data_section(ana, result_type=ana.analysis_type)

            display.check_p_sigma(p_ind_corr, sigma, show=False)
            display.check_p_sigma(p_ind_corr, sigma_slope * p_cal + sigma_null, label="fit")
                    
            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
