"""
python script/se3/se3_cal_result.py --ids 'cal-2018-se3-kk-75050_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.analysis import Analysis
from vpy.constants import Constants

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
            ana = Analysis(doc, init_dict=doc.get('Calibration').get('Analysis'))
            res = Result(doc)
            
            const = Constants(doc)
            
            p_cal = ana.pick('Pressure', 'cal', unit)

            conv = const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)
            res.ToDo.average_index
            #res.reject_outliers_index(res)    
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
