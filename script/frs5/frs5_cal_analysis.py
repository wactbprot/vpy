"""
python script/frs5/frs5_cal_analysis.py --ids 'cal-2018-frs5-kk-75001_0001' --db 'vl_db' --srv 'http://localhost:5984' #  -u
"""
import sys
import os
sys.path.append(".")

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal
from vpy.standard.frs5.uncert import Uncert
from vpy.device.cdg import InfCdg
import numpy as np
import matplotlib.pyplot as plt

from vpy.helper import init_customer_device, result_analysis_init

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1
        try:
            ids = args[idx_ids].split(';')
        except:
           fail = True

    if '-u' in args:
        update = True
    else:
        update = False

    if not fail and len(ids) >0:
        base_doc = io.get_base_doc("frs5")
        for id in ids:
            doc = io.get_doc_db(id)

            if update:
                doc = io.update_cal_doc(doc, base_doc)

            cus_dev = init_customer_device(doc)

            cal = Cal(doc)
            res = Analysis(doc)
            uncert = Uncert(doc)

            cal.temperature(res)
            cal.pressure_res(res)
            cal.pressure_cal(res)

            ## calculate the uncertainty of the standard
            uncert.total_standard(res)

            ## calculate customer indication
            gas = cal.Aux.get_gas()

            ## todo meas temp room, gas
            temperature_dict = {}

            offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )
            ind_dict = cal.Pres.get_dict('Type', 'ind' )

            offset = cus_dev.pressure(offset_dict, temperature_dict, unit = cal.unit, gas=gas)
            ind = cus_dev.pressure(ind_dict, temperature_dict, unit = cal.unit, gas=gas)
            res.store("Pressure", "offset", offset, cal.unit)
            res.store("Pressure", "ind", ind, cal.unit)
            res.store("Pressure", "ind_corr", ind - offset, cal.unit)

            # error for rating procedures
            ind = res.pick("Pressure", "ind_corr", cal.unit)
            cal = res.pick("Pressure", "cal" , cal.unit)
            res.store('Error', 'ind', ind/cal-1, '1')
            cus_dev.range_trans(res)

            io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
