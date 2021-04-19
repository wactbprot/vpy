"""
python script/frs5/frs5_cal_analysis_group_normal.py --ids 'cal-2020-frs5-ik-4050_0001'  -u  # --db 'vl_db' --srv 'http://localhost:5984'
"""
import sys
import os
sys.path.append(".")

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal
from vpy.standard.frs5.uncert import Uncert

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
            uncert.total_standard(res)
            gas = cal.Aux.get_gas()

            devs = (
                "1T_1", "1T_2", "1T_3",
                "5T_1",
                "10T_1", "10T_2", "10T_3",
                "50T_1",
                "100T_1", "100T_2", "100T_3",
                )

            p_cal = res.pick("Pressure", "cal", cal.unit)
            for dev in devs:
                p_offset = cal.Pres.get_value( '{}-offset'.format(dev), cal.unit)
                p_ind = cal.Pres.get_value('{}-ind'.format(dev), cal.unit)
                p_ind_corr = p_ind - p_offset
                res.store("Pressure", '{}-offset'.format(dev), p_offset, cal.unit)
                res.store("Pressure",'{}-ind'.format(dev), p_ind, cal.unit)
                res.store("Pressure",'{}-ind_corr'.format(dev), p_ind_corr, cal.unit)

                res.store('Error', '{}-ind'.format(dev), p_ind_corr/p_cal-1, '1')
                print(dev)
                print("----------------------------")

                print(p_ind_corr/p_cal-1)
            print("----------------------------")
            print("----------------------------")
            print(p_cal)
            io.save_doc(res.build_doc())

if __name__ == "__main__":
    main()
