"""
python script/frs5/frs5_cal_result.py --ids 'cal-2019-frs5-kk-75052_0003' 
"""
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

import copy
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.analysis import Analysis
from vpy.constants import Constants
from vpy.standard.frs5.uncert import Uncert  
from vpy.device.device import Device
from vpy.todo import ToDo
from vpy.device.srg import Srg
from vpy.device.cdg import Cdg
from vpy.device.qbs import Qbs

import matplotlib.pyplot as plt
def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}
    unit = 'Pa'
    result_type = "pressure_balance"

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split(';')
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
                customer_device = Srg(doc, customer_object)
            if customer_object.get("Class") == "CDG":
                customer_device = Cdg(doc, customer_object)
            if customer_object.get("Class") == "QBS":
                customer_device = Qbs(doc, customer_object)
            
            tdo = ToDo(doc)
            analysis = doc.get('Calibration').get('Analysis')
            
            ana = Analysis(doc, init_dict=analysis)
            res = Result(doc, result_type=result_type, skip=skip)
            
            # calculate customer uncertainty
            if "Uncertainty" in customer_object:
                # the function ana.total_uncert does not work
                # if uncert of standard does not exist already
                # hence:
                # 
                # --> skip_source="standard"
                u_dev = customer_device.get_total_uncert(meas=p_ind_corr, unit="Pa", runit="Pa", skip_source="standard")
                ana.store("Uncertainty", "device", u_dev/p_ind_corr, "1") 
            else:
                customer_device.offset_uncert(ana) 
                customer_device.repeat_uncert(ana) 
                customer_device.device_uncert(ana) 
           
            # combine u(standard) an u(device)
            ana.total_uncert() 

            # start build cert table
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)
            p_cal = ana.pick("Pressure", "cal", unit)
            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)

            m_x = p_ind_corr
            m_y = p_ind_corr/p_cal-1
            m_u = ana.pick("Uncertainty", "total_rel", "1")

            plt.xscale('symlog', linthreshx=1e-12)
            plt.errorbar(m_x, m_y,  yerr=m_u,  marker='o', linestyle="None", markersize=10, label="measurement")
            for i, v in enumerate(m_x):
                plt.text(v, m_y[i], i, rotation=45.)
            plt.legend()
            plt.grid()
            plt.show()

            ## reject points
            average_index, _ = ana.ask_for_reject(average_index=average_index)

            res.store_dict(quant="AuxValues", d={"AverageIndex": average_index}, dest=None, plain=True)
            c_x, c_y, c_u = res.make_error_table(ana, pressure_unit="Pa", error_unit='1', add_n_column=False)
            
            plt.xscale('symlog', linthreshx=1e-12)
            plt.plot(m_x, m_y,   marker='o', linestyle="None", markersize=10, label="certificate")
            plt.errorbar(c_x, c_y,  yerr=c_u,  marker='D', linestyle=":", markersize=10, label="certificate")            
            
            plt.legend()
            plt.grid()
            plt.show()
            
            res.make_measurement_data_section(ana, result_type=result_type)
            
            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
