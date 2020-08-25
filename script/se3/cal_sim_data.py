import sys
import os
import numpy as np
sys.path.append(os.environ["VIRTUAL_ENV"])
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal
from vpy.pkg_io import Io
from vpy.helper import init_customer_device

def main():

    io = Io()
    io.eval_args()
    doc = {"_id": "cal-sim-se3",
        "Calibration":{
                       "Measurement":{}}}


    ##-----------------------------------------
    ## standard
    ##-----------------------------------------
    base_doc = io.get_base_doc("se3")
    doc = io.update_cal_doc(doc, base_doc)

    vals = io.read_json("./vpy/standard/se3/values_sim.json")
    aux_vals = io.read_json("./vpy/standard/se3/meas_aux_values.json")
    ana_aux_vals = io.read_json("./vpy/standard/se3/ana_aux_values.json")

    doc['Calibration']['Measurement']['Values'] = vals
    doc['Calibration']['Measurement']['AuxValues'] = aux_vals


    ana = Analysis(doc, insert_dict={'AuxValues': ana_aux_vals}, analysis_type="expansion")

    cal = Cal(doc)
    cal.all(ana)
    Uncert(doc).total(ana)

    ##-----------------------------------------
    ## device
    ##-----------------------------------------
    doc['Calibration']['CustomerObject'] = {"Name": "0.1Torr_sim",
                                            "Type": "Kapazitives Membranvakuummeter",
                                            "Class": "CDG",
                                            "Setup": {"TypeHead": "0.1Torr",
                                                      "Unit": "Pa"},
                                            "Device": {"Producer": "MKS Instruments"},
                                            "Uncertainty":[{"Type":"digit",
                                                            "Value":2.9e-6,
                                                            "Unit":"Pa"}
                                                           ]}
    cus_dev = init_customer_device(doc)
    gas = "N2"

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

    io.save_doc(ana.build_doc())

if __name__ == "__main__":
    main()
