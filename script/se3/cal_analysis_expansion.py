"""
python script/se3/se3_cal_analysis_expansion.py --ids 'cal-2019-se3-kk-75002_0001'  # -a #--> new aux values
"""
import sys
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
from vpy.standard.se3.std import Se3
from vpy.standard.se3.uncert import Uncert
from vpy.helper import init_customer_device


def main():
    io = Io()
    io.eval_args()
    ret = {'ok':True}

    cmc = False
    base_doc = io.get_base_doc("se3")
    for id in io.ids:
        id = id.replace("\"", "")
        doc = io.get_doc_db(id)


        if io.update:
            doc = io.update_cal_doc(doc, base_doc)

        cal = Cal(doc)

        if io.auxval: ## get new the AuxValues from related (meas_date) state measurement
            meas_date = cal.Date.first_measurement()
            state_doc = io.get_state_doc("se3", date=meas_date)
            ana = Analysis(doc, analysis_type="expansion")

            cal.insert_state_results(ana, state_doc)
        else: ## keep AuxValues from Calibration.Analysis.AuxValues
            auxvalues = doc.get('Calibration').get('Analysis', {}).get('AuxValues', {})
            ana = Analysis(doc, insert_dict={'AuxValues': auxvalues}, analysis_type="expansion")

        cus_dev = init_customer_device(doc)

        uncert = Uncert(doc)

        cal.pressure_gn_corr(ana)
        cal.pressure_gn_mean(ana)
        cal.deviation_target_fill(ana)
        cal.temperature_before(ana)
        cal.temperature_after(ana)
        cal.temperature_room(ana)
        cal.temperature_gas_expansion(ana)
        cal.real_gas_correction(ana)
        cal.volume_add(ana)
        cal.volume_start(ana)
        cal.expansion(ana)
        cal.pressure_rise(ana)
        cal.correction_delta_height(ana)
        cal.correction_f_pressure(ana)
        cal.pressure_cal(ana)
        cal.error_pressure_rise(ana)
        cal.deviation_target_cal(ana)

        ## uncert. calculation
        if cmc:
            # bis update CMC Einträge --> vorh. CMC Einträge
            # cal uncertainty of standard
            uncert.cmc(ana)
        else:
            uncert.total(ana)

        ## calculate customer indication
        gas = cal.Aux.get_gas()
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

        if cal.ToDo.type == "error":
            ana.store('Error', 'ind', p_ind/p_cal-1, '1')
            cus_dev.range_trans(ana)

        if cal.ToDo.type == "sigma":
            ana.store('Error', 'ind', p_ind/p_cal-1, '1') ## used for check analysis
            ana.store('Sigma', 'eff', p_ind/p_cal, '1')

        io.save_doc(ana.build_doc())

    print(json.dumps(ret))

if __name__ == "__main__":
    main()
