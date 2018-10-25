"""
python se3_cal_uncertainty.py --ids 'cal-2018-se3-ik-4825_0001' --db 'vl_dd' --srv 'http://localhost:5984'
"""
import sys
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert

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
    
    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
            analysis = doc.get('Calibration', {}).get('Analysis', {})
            if 'Values' in analysis and 'Uncertainty' in analysis['Values']:
                analysis['Values']['Uncertainty'] = []
            res = Analysis(doc, init_dict=analysis)
            u = Uncert(doc)

            u.define_model()
            u.gen_val_dict(res)
            u.gen_val_array(res)

            u.volume_start(res)
            u.volume_5(res)
            u.temperature_before(res)
            u.temperature_after(res)
            u.pressure_fill(res)
            u.total(res)
            io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
