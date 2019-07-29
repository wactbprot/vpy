"""
python script/frs5/frs5_cal_analysis.py --ids 'cal-2018-frs5-kk-75001_0001' --db 'vl_db' --srv 'http://localhost:5984' #  -u 
"""
import sys
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal
from vpy.standard.frs5.uncert import Uncert
from vpy.device.cdg import InfCdg
import numpy as np
import matplotlib.pyplot as plt


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

            cal = Cal(doc)
            res = Analysis(doc)
            uncert = Uncert(doc)
        
            cal.temperature(res)
            cal.pressure_res(res)
            cal.pressure_cal(res)
            cal.pressure_offset(res)
            cal.pressure_ind(res)
            cal.error(res)
           
            io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
