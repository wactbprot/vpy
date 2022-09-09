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

from vpy.standard.ce3.uncert import Uncert

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

        cus_dev = init_customer_device(doc)
        cal = Cal(doc)
        uncert = Uncert(doc)
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
        cal.pressure_cal(ana)

        ## calculate customer indication
        offset_dict = cal.Pres.get_dict('Type', 'ind_offset' )
        ind_dict = cal.Pres.get_dict('Type', 'ind' )


        if cal.ToDo.type == "error":
            unit = cal.unit
        if cal.ToDo.type == "sens":
            unit = "A"

        offset = cus_dev.pressure(offset_dict, unit=unit)
        ind = cus_dev.pressure(ind_dict, unit=unit)

        ana.store("Pressure", "offset", offset, unit)
        ana.store("Pressure", "ind", ind, unit)
        ana.store("Pressure", "ind_corr", ind - offset, unit)

        p_cal = ana.pick("Pressure", "cal" , cal.unit)
        p_ind = ana.pick("Pressure", "ind_corr", unit)

        if cal.ToDo.type == "error":
            ana.store('Error', 'ind', p_ind/p_cal - 1, '1')

        if cal.ToDo.type == "sens":
            i_anode = cal.Curr.get_value("ind_anode", "A")
            i_faraday = cal.Curr.get_value("ind_faraday", "A")
            i_emis = cus_dev.get_value("ie", "mA") * cal.Cons.get_conv("mA", "A")
            if i_anode is not None and i_faraday is not None:
                i_emis = i_anode + i_faraday

            S = p_ind/(i_emis * p_cal)

            ana.store('Sensitivity', 'ind', S, '1')

        ## uncertanty
        ## fm3
        uncert.pressure_fill(ana)
        uncert.pressure_therm_transp(ana)
        uncert.delta_V(ana)
        uncert.delta_V_delta_t(ana)
        uncert.delta_t(ana)
        uncert.pressure_res(ana)
        ## fm3 total
        uncert.flow_pV(ana)
        ## ce3
        uncert.conductance(ana)
        uncert.flow_split(ana)
        uncert.temperature_fm(ana)
        uncert.temperature_uhv(ana)
        uncert.pressure_corr(ana)
        uncert.total(ana)
        io.save_doc(ana.build_doc())

    print(json.dumps(ret))

if __name__ == "__main__":
    main()
