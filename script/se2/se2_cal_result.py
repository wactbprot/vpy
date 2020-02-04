"""
python script/se2/se2_cal_result.py --srv 'http://a73434:5984' --db 'vl_db' --ids 'cal-2020-se2-kk-75015_0001' -s
"""
import sys
import os
sys.path.append(".")

import copy
import json
import numpy as np
import collections as cl
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.todo import ToDo
from vpy.values import Values
from vpy.analysis import Analysis
from vpy.constants import Constants
from vpy.standard.se2.uncert import Uncert as UncertSe2
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
            
            if "Values" in analysis and "Uncertainty" in analysis["Values"]:
                del analysis["Values"]["Uncertainty"]

            ana = Analysis(doc, init_dict=analysis)
            se2_uncert = UncertSe2(doc)            
            
            result_type = analysis.get("AnalysisType", "default")
            result_type = "se2_expansion_direct"
            res = Result(doc, result_type=result_type)
            
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)
            p_off = ana.pick('Pressure', 'offset', unit)

            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)
            print(average_index)
            average_index = ana.coarse_error_filtering(average_index=average_index)
            print(average_index)
            average_index, ref_mean, ref_std, loops = ana.fine_error_filtering(average_index=average_index)
            pressure_range_index = ana.make_pressure_range_index(ana, average_index)

            print(average_index)
            print(ref_mean)
            print(ref_std)
            print(loops)

            if result_type == "se2_expansion_direct" and tdo.type == "error":
                average_index, reject_index = ana.ask_for_reject(average_index=average_index)
                reject_index_offset = ana.ask_for_reject_offset(average_index=average_index)
                d = {
                    "AverageIndex": average_index,
                    "AverageIndexFlat": ana.flatten(average_index),
                    "PressureRangeIndex": pressure_range_index,
                    "RejectIndex": reject_index,
                    "RejectIndexOffset": reject_index_offset
                    }

                p_tdo, p_tdo_unit = tdo.Pres.get_value_and_unit("target")
                conv = res.Const.get_conv(from_unit=p_tdo_unit, to_unit="Pa")

                p_tdo = conv * p_tdo
                p_tdo_evis = [p_tdo[i] for i in range(len(p_tdo)) if p_tdo[i] < 95]

                if len(p_tdo_evis) > 1:
                    e_vis, cf_vis, u_vis, vis_unit = ana.ask_for_evis()
                    d["Evis"] = e_vis
                    d["CFvis"] = cf_vis
                    d["Uvis"] = u_vis
                    d["VisUnit"] =vis_unit

                ana.store_dict(quant="AuxValues", d=d, dest=None, plain=True)
                res.store_dict(quant="AuxValues", d=d, dest=None, plain=True)

                se2_uncert.u_PTB_rel(ana)
                se2_uncert.make_offset_stability(ana)
            
                customer_device.repeat_uncert(ana) 
                customer_device.device_uncert(ana) 
                
                ana.total_uncert() 
                u = ana.pick("Uncertainty", "total_rel", "1")            
            print(customer_device.doc)
            print("ffffffffffffffffffffffffffffff")
            print(tdo.type)
            print(result_type)
            if result_type == "se2_expansion_direct" and tdo.type == "sigma":
                
                
                p_ind_corr =  np.take(p_ind_corr, ana.flatten(average_index))
                p_cal =  np.take(p_cal, ana.flatten(average_index))
                p_off =  np.take(p_off, ana.flatten(average_index))
                d = {
                    "AverageIndex": average_index,
                    "AverageIndexFlat": ana.flatten(average_index)
                }                
                print(p_ind_corr)
                print(p_cal)
                #u =  np.delete(u, skip)
                sigma_null, sigma_slope, sigma_std = customer_device.sigma_null(p_cal=p_cal, cal_unit=unit, p_ind=p_ind_corr, ind_unit=unit)
                d["SigmaNull"]  = sigma_null
                d["SigmaCorrSlope"] = np.abs(sigma_slope/sigma_null)
                d["SigmaStd"] = sigma_std

                # aux_values_pres = Values(doc.get('Calibration').get('Measurement').get("AuxValues").get("Pressure"))
                # rd, rd_unit = aux_values_pres.get_value_and_unit(d_type="offset")
                # d["OffsetMean"] = np.nanmean(rd)
                # d["OffsetStd"] = np.nanstd(rd)
                # d["OffsetUnit"] = rd_unit
             
                ana.store_dict(quant="AuxValues", d=d, dest=None, plain=True)
                res.store_dict(quant="AuxValues", d=d, dest=None, plain=True)

            maesurement_date = cl.Counter(doc["Calibration"]["Measurement"]["Values"]["Date"]["Value"]).most_common(1)[0][0]
            doc["Calibration"]["Measurement"]["Date"] = [{"Type": "measurement", "Value": [maesurement_date]}]
            
            res.make_measurement_data_section(ana, result_type=result_type)

            if tdo.type == "error":
                # start build cert table
                p_ind, err, u =res.make_error_table(ana, pressure_unit=unit, error_unit='1')

            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
