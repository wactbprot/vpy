"""
script works for SE3, FRS and DKM measurements

python script/se3/cal_result_error.py --ids 'cal-2020-se3-kk-75012_0001' --db 'vl_db_work' --srv 'http://localhost:5984'
"""
import sys
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.display.se3 import SE3 as Display
from vpy.todo import ToDo
from vpy.helper import init_customer_device, result_analysis_init

def main():
    io = Io()
    io.eval_args()
    ret = {'ok':True}

    cmc = True#False
    for id in io.ids:
        doc = io.get_doc_db(id)
        tdo = ToDo(doc)

        if tdo.type != "error":
            sys.exit("wrong script")

        display = Display(doc)
        cus_dev = init_customer_device(doc)
        ana = result_analysis_init(doc)

        ## generate result instance with analysis res type
        ## set skip flag to ignore result for cert
        result_type = ana.analysis_type
        std = doc.get("Calibration").get("Standard").get("Name")
        if std == "FRS5":
            result_type = "pressure_balance"
        if std == "DKM_PPC4":
            result_type = "rotary_piston_gauge"

        res = Result(doc, result_type=result_type, skip=io.skip)

        p_cal = ana.pick('Pressure', 'cal', ana.pressure_unit)
        p_ind_corr = ana.pick('Pressure', 'ind_corr', ana.pressure_unit)
        err = ana.pick("Error", "ind", "1")

        conv = res.Const.get_conv(from_unit=ana.pressure_unit, to_unit=tdo.pressure_unit)
        average_index = tdo.make_average_index(p_cal*conv, tdo.pressure_unit)


        ## will be filled up with aux values:
        d = {}

        display.check_outlier_err(ana)
        average_index, reject_index  = ana.ask_for_reject(average_index=average_index)
        flat_average_index = ana.flatten(average_index)

        ## offset contrib
        cus_dev.offset_uncert(ana,  reject_index =  reject_index)

        ## default uncert. contrib.  repeat
        cus_dev.repeat_uncert(ana)

        ## add. uncert. contrib.
        if "uncert_dict" in dir(cus_dev):
            ## e.g. for digitalisation uncert.
            u_add = cus_dev.get_total_uncert(meas_vec=p_ind_corr,
                                             meas_unit=ana.pressure_unit,
                                             return_unit=ana.pressure_unit,
                                             res=ana,
                                             skip_source="standard",
                                             prefix=False)
        cus_dev.device_uncert(ana)

        d["AverageIndex"] = average_index
        d["AverageIndexFlat"] = flat_average_index
        ana.store_dict(quant='AuxValues', d=d, dest=None)

        ## rm values
        p_cal = np.take(p_cal, flat_average_index)
        p_ind_corr = np.take(p_ind_corr, flat_average_index)
        err = np.take(err, flat_average_index)

        ## store reduced quant. for plot
        ana.store("Pressure", "red_ind_corr", p_ind_corr, ana.pressure_unit, dest="AuxValues")
        ana.store("Pressure", "red_cal", p_cal, ana.pressure_unit, dest="AuxValues")
        ana.store("Error", "red_ind", err, "1", dest="AuxValues")

        # get from customer object
        temperature_head, head_unit = ana.ask_for_head_temperature(temperature_head=45.0)
        if temperature_head:
            ## e_vis fit
            params = cus_dev.get_e_vis_fit_params(p_cal, err)
            err_model = cus_dev.e_vis_model(p_cal, *params)
            ana.store("Error", "model", err_model, "1", dest="AuxValues")

            ## cal. e_vis (fit)
            e_vis_cal = cus_dev.e_vis_model(100., *params)
            d["EvisFitParams"] = params
            d["EvisModel"] = float(e_vis_cal)
            ana.store_dict(quant='AuxValues', d=d, dest=None)
            display.plot_e_vis_model(ana)

            ## ask for e_vis
            e_vis, cf_vis, u_vis, vis_unit = ana.ask_for_evis(e_vis_cal)
            d["Evis"] = float(e_vis)
            d["CFvis"] = cf_vis
            d["Uvis"] = u_vis
            d["VisUnit"] = vis_unit
            ana.store_dict(quant='AuxValues', d=d, dest=None)

            ## plot cert evis
            display.plot_e_vis(ana)

            ## cal. temperature norm.
            t_head = temperature_head + res.Const.get_conv(from_unit=head_unit, to_unit="K")
            t_head_dict = {"Value":t_head, "Unit":"K"}
            tdo_unit = tdo.temperature_unit
            t_target = tdo.Temp.get_value("target", tdo_unit) + res.Const.get_conv(from_unit=tdo_unit, to_unit="K")
            t_norm_dict = {"Value":t_target, "Unit":"K"}
            e_dict = ana.pick_dict("Error", "ind")
            p_cal_dict = ana.pick_dict('Pressure', 'cal')
            t_gas_dict = ana.pick_dict("Temperature", "after")
            t_room_dict = ana.pick_dict("Temperature", "room")

            ## float() avoids that the value becomes an array
            d["TemperatureHead"] = float(t_head[0])
            d["TemperatureHeadUnit"] = "K"
            d["TemperatureNorm"] = float(t_target[0])
            d["TemperatureNormUnit"] = "K"
            ana.store_dict(quant='AuxValues', d=d, dest=None)

            err_norm = cus_dev.temperature_correction(e_dict, p_cal_dict, t_gas_dict, t_head_dict, t_norm_dict, e_vis, vis_unit)
            ana.store("Error", "ind_temperature_corr",  err_norm, e_dict.get("Unit"))
            ana.store("Error", "red_ind_temp_corr", np.take(err_norm,  flat_average_index), "1", dest="AuxValues")

            display.plot_err_diff(ana)


        ## the uncertainty of the standard is
        # already calculated at analysis step
        ana.total_uncert()

        ## store red version for plot
        u_rep = ana.pick("Uncertainty", "repeat", "1")
        u_off = ana.pick("Uncertainty", "offset", "1")
        u_tot = ana.pick("Uncertainty", "total_rel", "1")
        u_dev = ana.pick("Uncertainty", "device", "1")
        u_std = ana.pick("Uncertainty", "standard", "1")

        ana.store("Uncertainty", "red_u_rep", np.take(u_rep, flat_average_index), "1", dest="AuxValues")
        ana.store("Uncertainty", "red_u_std", np.take(u_std, flat_average_index), "1", dest="AuxValues")
        ana.store("Uncertainty", "red_u_dev", np.take(u_dev, flat_average_index), "1", dest="AuxValues")
        ana.store("Uncertainty", "red_u_tot", np.take(u_tot, flat_average_index), "1", dest="AuxValues")
        ana.store("Uncertainty", "red_u_off", np.take(u_off, flat_average_index), "1", dest="AuxValues")

        display.plot_uncert(ana)

        # start making data sections
        res.make_measurement_data_section(ana, result_type=result_type)

        # start build cert table
        p_cal_mv, p_ind_mv, err_mv, u_mv = res.make_error_table(ana, pressure_unit=ana.pressure_unit, error_unit='1')

        ana.store("Pressure", "ind_mean", p_ind_mv, ana.pressure_unit , dest="AuxValues")
        ana.store("Error", "ind_mean", err_mv, "1", dest="AuxValues")
        ana.store("Uncertainty", "total_mean", u_mv, "1", dest="AuxValues")

        display.plot_mean(ana)

        res.check_error_column(ana)
        
        doc = ana.build_doc("Analysis", doc)
        doc = res.build_doc("Result", doc)

        io.save_doc(doc)

if __name__ == "__main__":
    main()
