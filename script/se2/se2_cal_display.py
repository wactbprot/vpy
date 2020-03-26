"""
python script/se2/se2_cal_display.py --db 'vl_db' --srv 'http://a73434:5984' --ids 'cal-2020-se2-kk-75015_0001'
"""
import sys
import os
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.display import Display
from vpy.standard.se2.cal import Cal

from vpy.standard.se2.std import Se2

from vpy.device.cdg import InfCdg, Cdg
from vpy.device.srg import Srg
from vpy.device.rsg import Rsg


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
            date = "2019-07-10"#doc[""]
            pn_doc1 = io.get_pn_by_date(std="se2", date=date, cert="9911")
            pn_doc2 = io.get_pn_by_date(std="se2", date=date, cert="0118")

            disp = Display(doc)
            disp.SE2_CDG_error_plot().show()
            disp.SE2_CDG_offset_abs().show()
            disp.SE2_CDG_offset_rel().show()
            disp.SE2_CDG_error_reject().show()

    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()