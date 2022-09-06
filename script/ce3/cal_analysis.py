"""
python script/ce3/cal_analysis.py --ids 'cal-2021-ce3-kk-75458_0001' -u #
"""
import sys
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.ce3.cal import Cal
from vpy.standard.ce3.std import Ce3
from vpy.helper import init_customer_device

def main():
    io = Io()
    io.eval_args()
    ret = {'ok':True}

    cmc = True
    base_doc = io.get_base_doc("ce3")
    for id in io.ids:
        id = id.replace("\"", "")
        doc = io.get_doc_db(id)

        if io.update:
            doc = io.update_cal_doc(doc, base_doc)

        cal = Cal(doc)
        ana = Analysis(doc)

        cal.pressure_fill(ana)
        cal.pressure_dp(ana)
        cal.drift(ana)
        cal.conductance(ana)
        cal.conductance_name(ana)
        cal.conductance_extrap(ana)
        cal.temperature_pbox(ana)
        cal.temperature_fm(ana)
        cal.temperature_uhv(ana)
        cal.temperature_xhv(ana)
        cal.temperature_room(ana)
        cal.flow(ana)
        cal.mean_free_path(ana)

        io.save_doc(ana.build_doc())

    print(json.dumps(ret))

if __name__ == "__main__":
    main()
