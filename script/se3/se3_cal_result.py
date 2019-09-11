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

    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
            
            customer_object = doc.get('Calibration').get('CustomerObject')
            if customer_object.get("Class") == "SRG":
                customer_device = Srg(doc, customer_object)
            if customer_object.get("Class") == "CDG":
                customer_device = Cdg(doc, customer_object)
            tdo = ToDo(doc)
            analysis = doc.get('Calibration').get('Analysis')
            ana = Analysis(doc, init_dict=analysis)
            
            result_type = analysis.get("AnalysisType", "default")
            res = Result(doc, result_type=result_type)
            
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)
            
            if "Uncertainty" in customer_object:
                
                u_dev = customer_device.get_total_uncert(meas=p_ind_corr, unit="Pa", runit="Pa", res=ana, skip_source="standard")
                ana.store("Uncertainty", "device", u_dev/p_ind_corr, "1") 
            else:
                customer_device.offset_uncert(ana) 
                customer_device.repeat_uncert(ana) 
                customer_device.device_uncert(ana) 

            ## the uncertainty of the standard is 
            # already calculated at analysis step            
            ana.total_uncert() 
            u = ana.pick("Uncertainty", "total_rel", "1")

            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)

            # plot to rm outliers and check
            if tdo.type == "error":
                x = p_ind_corr
                y = p_ind_corr/p_cal-1

            if tdo.type == "sigma":
                x = p_ind_corr
                y = p_ind_corr/p_cal
               
            plt.xscale('symlog', linthreshx=1e-12)
            plt.errorbar(x, y,  yerr=u,  marker='o', linestyle="None", markersize=10, label="measurement")
            for i, v in enumerate(x):
                plt.text(v, y[i], i, rotation=45.)
            plt.show()

            if result_type == "direct" and tdo.type == "error":
                average_index, _ = ana.ask_for_reject(average_index=average_index)
                d = {"AverageIndex": average_index}


            if result_type == "expansion" and tdo.type == "error":
                average_index, _ = ana.ask_for_reject(average_index=average_index)
                d = {"AverageIndex": average_index}

                e_vis, cf_vis, u_vis, vis_unit = ana.ask_for_evis()
                d["Evis"] = e_vis
                d["CFvis"] = cf_vis
                d["Uvis"] = u_vis
                d["VisUnit"] =vis_unit

            if result_type == "expansion" and tdo.type == "sigma":
                skip = ana.ask_for_skip()
                d = {"SkipIndex":skip}
                
                p_ind_corr = np.delete(p_ind_corr, skip)
                p_cal = np.delete(p_cal, skip)
                u = np.delete(u, skip)
                sigma_null, sigma_slope, sigma_std = customer_device.sigma_null(p_cal=p_cal, cal_unit=unit, p_ind=p_ind_corr, ind_unit=unit)
                d["SigmaNull"]  = sigma_null
                d["SigmaCorrSlope"] = np.abs(sigma_slope/sigma_null)
                d["SigmaStd"] = sigma_std

                aux_values_pres = Values(doc.get('Calibration').get('Measurement').get("AuxValues").get("Pressure"))
                rd, rd_unit = aux_values_pres.get_value_and_unit(d_type="offset")
                d["OffsetMean"] = np.nanmean(rd)
                d["OffsetStd"] = np.nanstd(rd)
                d["OffsetUnit"] = rd_unit

            res.store_dict(quant="AuxValues", d=d, dest=None, plain=True)
                
            # start making data sections
            ## obsolet res.make_calibration_data_section(ana)
            res.make_measurement_data_section(ana, result_type=result_type)

            if tdo.type == "error":
                # start build cert table
                p_ind, err, u =res.make_error_table(ana, pressure_unit=unit, error_unit='1')
            
                plt.subplot(111)
                plt.xscale('symlog', linthreshx=1e-12)
                plt.errorbar(p_ind, err,   yerr=u,  marker='8', linestyle=":", markersize=10, label="certificate")

                plt.legend()
                plt.title('Calib. of {}@SE3'.format(customer_object.get('Name')))
                plt.ylabel('$e$')
                plt.grid(True)
                plt.show()
            
            if tdo.type == "sigma":
                def lin_reg(p):
                    return sigma_slope * p + sigma_null 
               
                plt.subplot(111)
                plt.errorbar(p_cal, p_ind_corr/p_cal,   yerr=u*p_ind_corr/p_cal,  marker='8', linestyle=":", markersize=10, label="certificate")
                plt.plot(p_cal, lin_reg(p_cal), linestyle="-" )
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
