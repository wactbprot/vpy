"""
python script/se3/se3_cal_result.py --ids 'cal-2018-se3-kk-75050_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
import copy
import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.analysis import Analysis
from vpy.constants import Constants
from vpy.standard.se3.uncert import Uncert as UncertSe3 
from vpy.device.device import Device

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
            
            customer_device = Device(doc, doc.get('Calibration').get('CustomerObject'))
            ana = Analysis(doc, init_dict=doc.get('Calibration').get('Analysis'))
            res = Result(doc)
            
            p_cal = ana.pick('Pressure', 'cal', unit)
            p_ind_corr = ana.pick('Pressure', 'ind_corr', unit)

            ## bis update CMC Einträge --> vorh. CMC Einträge  
            # cal uncertainty of standard
            ## uncert = Uncert(doc)
            ## uncert.define_model()
            ## uncert.gen_val_dict(ana)
            ## uncert.gen_val_array(ana)
            ## uncert.volume_start(ana)
            ## uncert.volume_5(ana)
            ## uncert.pressure_fill(ana)
            ## uncert.temperature_after(ana)
            ## uncert.temperature_before(ana)
            ## uncert.expansion(ana)
            ## uncert.total(ana)
            ## uncert_standard = ana.pick(quant='Uncertainty', dict_type='standard', dict_unit='1')
            ## # cal uncertaity of the costomer device
            ## uncert_customer = customer_device.get_total_uncert(meas=p_ind_corr, unit=unit, runit=unit)/p_cal
            ## ana.store(quant="Uncertainty", type="customer", value=uncert_customer, unit='1')
            ## # combine customer and standard uncertainty
            ## uncert_total = np.sqrt( np.power(uncert_customer, 2) + np.power(uncert_standard, 2) )
            ## ana.store(quant="Uncertainty", type="total_rel", value= uncert_total, unit='1')
            ## ana.store(quant="Uncertainty", type="total_abs", value= uncert_total*p_cal, unit=unit)

            # start build cert table
            conv = res.Const.get_conv(from_unit=unit, to_unit=res.ToDo.pressure_unit)
            average_index = res.ToDo.make_average_index(p_cal*conv, res.ToDo.pressure_unit)

            average_index = ana.coarse_error_filtering(average_index=average_index)
            average_index, ref_mean, ref_std, loops = ana.fine_error_filtering(average_index=average_index)
            # plot needed
            average_index = ana.ask_for_reject(average_index=average_index)
            
            ana.store_dict(quant="AuxValues", d={"AverageIndex": average_index}, dest=None, plain=True)
       
            se3_uncert = UncertSe3(doc)

            se3_uncert.offset(ana)
            se3_uncert.repeat(ana)
            se3_uncert.cmc(ana)
 
            se3_uncert.total(ana)

            res.make_error_table(ana, pressure_unit='Pa', error_unit='1')
            
            doc = ana.build_doc("Analysis", doc)
            doc = res.build_doc("Result", doc)
            io.save_doc(doc)
       
    else:
        ret = {"error": "no --ids found"}

if __name__ == "__main__":
    main()
