"""
python script/frs5-dkm_ppc4/vg_analysis.py --ids 'cal-2022-frs5|dkm_ppc4-vg-9999_0001' --db 'vl_db'  -u
"""
import sys
import os
import json
sys.path.append(".")

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal as CalFRS5
from vpy.standard.frs5.uncert import Uncert as UncertFRS5

from vpy.standard.dkm_ppc4.cal import Cal as CalDKM
from vpy.standard.dkm_ppc4.uncert import Uncert as UncertDKM

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
            ids = args[idx_ids].split('@')
        except:
           fail = True

    if '-u' in args:
        update = True
    else:
        sys.exit("dont work without update")

    if not fail and len(ids) > 0:
        base_doc_frs5 = io.get_base_doc("frs5")
        base_doc_dkm = io.get_base_doc("dkm_ppc4")
        for id in ids:
            doc = io.get_doc_db(id)

#            if update:
#                doc = io.update_cal_doc(doc, base_doc_frs5)

            ## frs5
            doc = io.update_cal_doc(doc, base_doc_frs5)
            ana = Analysis(doc)
            cal = CalFRS5(doc)
            uncert = UncertFRS5(doc)

            cal.temperature(ana)
            cal.pressure_res(ana)
            cal.pressure_cal(ana)

            ## calculate the uncertainty of the standard
            uncert.total_standard(ana)

            p_cal = ana.pick("Pressure", "cal", "Pa")
            u_cal = ana.pick("Uncertainty", "standard", "1")

            ana.store("Pressure", "cal_frs5", p_cal, "Pa")
            ana.store("Uncertainty", "standard_frs5", u_cal, "1")

            ## dkm
            doc = io.update_cal_doc(doc, base_doc_dkm)
            ana = Analysis(doc)

            cal = CalDKM(doc)
            uncert = UncertDKM(doc)

            cal.temperature(ana)
            cal.temperature_correction(ana)
            cal.pressure_res(ana)
            cal.pressure_cal_uncorr(ana)
            cal.pressure_cal(ana)

            # cal uncert of standard
            uncert.total(ana)

            p_cal = ana.pick("Pressure", "cal", "Pa")
            u_cal = ana.pick("Uncertainty", "standard", "1")

            ana.store("Pressure", "cal_dkm_ppc4", p_cal, "Pa")
            ana.store("Uncertainty", "standard_dkm_ppc4", u_cal, "1")



            io.save_doc(ana.build_doc())

    print(json.dumps(ret))

if __name__ == "__main__":
    main()
