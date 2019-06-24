"""
python script/se3/se3_cal_result.py --ids 'cal-2018-se3-kk-75050_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

import copy
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.todo import ToDo
from vpy.analysis import Analysis
from vpy.constants import Constants
from vpy.standard.se3.uncert import Uncert as UncertSe3 
from vpy.device.device import Device
import matplotlib.pyplot as plt
def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}
    unit = 'Pa'

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split(';')
        except:
           fail = True

    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
            
            customer_object = doc.get('Calibration').get('CustomerObject')
            customer_device = Device(doc, customer_object)
            tdo = ToDo(doc)
            analysis = doc.get('Calibration').get('Analysis')
            
            if "Values" in analysis and "Uncertainty" in analysis["Values"]:
                del analysis["Values"]["Uncertainty"]
            ana = Analysis(doc, init_dict=analysis)

            result_type = analysis.get("AnalysisType", "default")
            res = Result(doc, result_type=result_type)
            
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)

            # bis update CMC Einträge --> vorh. CMC Einträge  
            # cal uncertainty of standard
            ## uncert = Uncert(doc)
            ## uncert.define_model()
            ## uncert.gen_val_dict(ana)
            ## uncert.gen_val_array(ana)
            ## uncert.volume_start(ana)
            ## uncert.volume_5(ana)
            ## uncert.pressure_fill(ana)
            ## uncert.temperature_after(ana)
            ## uncert.temperature_before(ana)
            ## uncert.expansion(ana)
            ## uncert.total(ana)
            ## uncert_standard = ana.pick(quant='Uncertainty', dict_type='standard', dict_unit='1')
            
            se3_uncert = UncertSe3(doc)
            if "Uncertainty" in customer_object:
                u_dev = customer_device.get_total_uncert(meas=p_ind_corr, unit="Pa", runit="Pa")
                ana.store("Uncertainty", "device", u_dev/p_ind_corr, "1") 
            else:
                se3_uncert.offset(ana)
                se3_uncert.repeat(ana)
                offset_uncert = ana.pick("Uncertainty", "offset", "1")
                repeat_uncert = ana.pick("Uncertainty", "repeat", "1")
                ana.store("Uncertainty", "device", np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2)), "1")
            
            se3_uncert.cmc(ana)
            se3_uncert.total(ana)
            u = ana.pick("Uncertainty", "total_rel", "1")
            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)
            average_index = ana.coarse_error_filtering(average_index=average_index)
            average_index, ref_mean, ref_std, loops = ana.fine_error_filtering(average_index=average_index)

            # plot to rm outliers and check
            if tdo.type == "error":
                x = p_ind_corr
                y = p_ind_corr/p_cal-1
            if tdo.type = "sigma":
                x = p_ind_corr
                y = p_ind_corr/p_cal
                
            plt.xscale('symlog', linthreshx=1e-12)
            plt.errorbar(x, y,  yerr=u,  marker='o', linestyle="None", markersize=10, label="measurement")
            for i, v in enumerate(x):
                plt.text(v, y[i], i, rotation=45.)
            plt.show()

            average_index = ana.ask_for_reject(average_index=average_index)
            d = {"AverageIndex": average_index}

            if result_type == "expansion" and tdo.type == "error":
                e_vis, cf_vis, u_vis, vis_unit = ana.ask_for_evis()
                d["Evis"] = e_vis,
                d["CFvis"] = cf_vis,
                d["Uvis"] = u_vis,
                d["VisUnit"] =vis_unit

            if result_type == "expansion" and tdo.type == "sigma":
                sigma_null, sigma_slope = customer_device.sigma_null(x=p_ind_corr, x_unit=unit, y=p_cal, y_unit=unit)
                d["SigmaNull"]  = sigma_null
                d["SigmaSlope"] = sigma_slope

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
            if tdo.type == "sigma ":
                # next ---
                pass

            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
