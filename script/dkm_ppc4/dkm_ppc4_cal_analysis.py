"""
python script/dkm_ppc4/dkm_ppc4_cal_analysis.py --ids 'cal-2018-dkm_ppc4-kk-75001_0001' --db 'vl_db' --srv 'http://localhost:5984' #  -u
"""
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.dkm_ppc4.cal import Cal
from vpy.standard.dkm_ppc4.uncert import Uncert

import numpy as np
from vpy.helper import init_customer_device

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
        base_doc = io.get_base_doc("dkm_ppc4")
        for id in ids:
            doc = io.get_doc_db(id)

            if update:
                doc = io.update_cal_doc(doc, base_doc)

            cus_dev = init_customer_device(doc)

            res = Analysis(doc)
            uncert = Uncert(doc)
            cal = Cal(doc)
            cal.temperature(res)
            cal.temperature_correction(res)
            cal.pressure_res(res)
            cal.mass_total(res)
            cal.pressure_cal(res)

            # cal uncert of standard
            uncert.total(res)

            ## calculate customer indication
            gas = cal.Aux.get_gas()
            ## todo meas temp room, gas
            temperature_dict = {}

            offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )
            ind_dict = cal.Pres.get_dict('Type', 'ind' )

            offset = cus_dev.pressure(offset_dict, temperature_dict, unit = cal.unit, gas=gas)
            ind = cus_dev.pressure(ind_dict, temperature_dict, unit = cal.unit, gas=gas)

            ind_corr = ind - offset

            res.store("Pressure", "offset", offset, cal.unit)
            res.store("Pressure", "ind", ind, cal.unit)
            res.store("Pressure", "ind_corr", ind_corr , cal.unit)

            # error for rating procedures
            p_ind_corr = res.pick("Pressure", "ind_corr", cal.unit)
            p_cal = res.pick("Pressure", "cal" , cal.unit)
            res.store('Error', 'ind', p_ind_corr/p_cal-1, '1')
            cus_dev.range_trans(res)

            print(p_ind_corr/p_cal-1)
            io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
