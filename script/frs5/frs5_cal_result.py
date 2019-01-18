import sys
import copy
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.analysis import Analysis
from vpy.constants import Constants
from vpy.standard.frs5.uncert import Uncert  
from vpy.device.device import Device

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}
    unit = 'mbar'

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split(';')
        except:
           fail = True

    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
            
            customer_device = Device(doc, doc.get('Calibration').get('CustomerObject'))
            ana = Analysis(doc, init_dict=doc.get('Calibration').get('Analysis'))
            res = Result(doc)

            uncert = Uncert(doc)
            uncert.total_standard(ana)
       
            uncert.offset(ana)
            uncert.repeat_rel(ana)
            uncert.total(ana)

            # start build cert table
            p_cal = ana.pick("Pressure", "cal", unit)
            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)
            average_index = ana.coarse_error_filtering(average_index=average_index)
            average_index, ref_mean, ref_std, loops = ana.fine_error_filtering(average_index=average_index)
            # plot needed
            average_index = ana.ask_for_reject(average_index=average_index)
            
            ana.store_dict(quant="AuxValues", d={"AverageIndex": average_index}, dest=None, plain=True)

            res.make_error_table(ana, pressure_unit="Pa", error_unit='1', add_n_column=True)
            
            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
