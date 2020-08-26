import sys
import os
import json
import numpy as np
sys.path.append(os.environ["VIRTUAL_ENV"])
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal
from vpy.pkg_io import Io
from vpy.helper import init_customer_device

def main(io, config):


    io.eval_args()
    doc = {"_id": "cal-sim-se3",
        "Calibration":{
                       "Measurement":{}}}
    struct_path = config.get("struct_path")
    values_file = config.get("values_file")
    cal_file = config.get("cal_file")

    ##-----------------------------------------
    ## standard
    ##-----------------------------------------
    base_doc = io.get_base_doc("se3")
    doc = io.update_cal_doc(doc, base_doc)

    vals = io.read_json("{}/{}".format(struct_path, values_file))
    aux_vals = io.read_json("{}/meas_aux_values.json".format(struct_path))
    ana_aux_vals = io.read_json("{}/ana_aux_values.json".format(struct_path))

    doc['Calibration']['Measurement']['Values'] = vals
    doc['Calibration']['Measurement']['AuxValues'] = aux_vals

    ana = Analysis(doc, insert_dict={'AuxValues': ana_aux_vals}, analysis_type="expansion")

    cal = Cal(doc)
    cal.all(ana)
    Uncert(doc).total(ana)

    ##-----------------------------------------
    ## device
    ##-----------------------------------------
    doc['Calibration']['CustomerObject'] = config.get("customer_object")
    cus_dev = init_customer_device(doc)
    gas = config.get("gas")

    temperature_dict = ana.pick_dict('Temperature', 'after')
    offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )
    ind_dict = cal.Pres.get_dict('Type', 'ind' )
    range_dict = cal.Range.get_dict('Type', 'ind' )

    offset = cus_dev.pressure(offset_dict, temperature_dict, range_dict=range_dict, unit = cal.unit, gas=gas)
    ind = cus_dev.pressure(ind_dict, temperature_dict, range_dict=range_dict, unit = cal.unit, gas=gas)
    ana.store("Pressure", "offset", offset, cal.unit)
    ana.store("Pressure", "ind", ind, cal.unit)
    ana.store("Pressure", "ind_corr", ind - offset, cal.unit)

    p_ind = ana.pick("Pressure", "ind_corr", cal.unit)
    p_cal = ana.pick("Pressure", "cal" , cal.unit)
    ana.store('Error', 'ind', p_ind/p_cal-1, '1')
    cus_dev.range_trans(ana)

    cus_dev.offset_uncert(ana)
    cus_dev.repeat_uncert(ana)

    if "uncert_dict" in dir(cus_dev):
        u_add = cus_dev.get_total_uncert(meas_vec=p_ind,
                                        meas_unit=ana.pressure_unit,
                                        return_unit=ana.error_unit,
                                        res=ana,
                                        skip_source="standard",
                                        prefix=False)
    cus_dev.device_uncert(ana)

    ana.total_uncert()


    with open("{}/{}".format(struct_path, cal_file), 'w') as f:
        json.dump(ana.build_doc(), f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    with open('./script/se3/sim_config.json') as f:
        config = json.load(f)

    io = Io()
    main(io, config)
