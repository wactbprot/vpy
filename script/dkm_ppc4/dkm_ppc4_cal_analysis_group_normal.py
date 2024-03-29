"""
python script/dkm_ppc4/dkm_ppc4_cal_analysis.py --ids 'cal-2018-dkm_ppc4-kk-75001_0001' --db 'vl_db' --srv 'http://localhost:5984' #  -u
"""
import sys
import os
sys.path.append(".")

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.dkm_ppc4.cal import Cal
from vpy.standard.dkm_ppc4.uncert import Uncert

import numpy as np

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

            res = Analysis(doc)

            cal = Cal(doc)
            cal.temperature(res)
            cal.temperature_correction(res)
            cal.pressure_res(res)
            cal.mass_total(res)
            cal.pressure_cal(res)

            # cal uncert of standard
            uncert = Uncert(doc)
            uncert.total(res)

            ## calculate customer indication
            gas = cal.Aux.get_gas()

            devs = ("50T_1",
                    "100T_1", "100T_2", "100T_3",
                    "500T_1",
                    "1000T_1", "1000T_2", "1000T_3",)

            p_cal = res.pick("Pressure", "cal", cal.unit)
            for dev in devs:
                p_offset = cal.Pres.get_value( '{}-offset'.format(dev), cal.unit)
                p_ind = cal.Pres.get_value('{}-ind'.format(dev), cal.unit)
                e = p_ind/p_cal-1
                print("----------------")
                print(dev)
                print(p_cal)
                print(e)
                res.store("Pressure", '{}-offset'.format(dev), p_offset, cal.unit)
                res.store("Pressure",'{}-ind'.format(dev), p_ind, cal.unit)
                res.store("Pressure",'{}-ind_corr'.format(dev), p_ind - p_offset, cal.unit)

                res.store('Error', '{}-ind'.format(dev), e, '1')

            io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
