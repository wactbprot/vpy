"""
python script/ce3/cal_result_error.py --ids 'cal-2021-ce3-kk-75421_0001' --db 'vl_db' --srv 'http://localhost:5984'
"""
import sys
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.result import Result
from vpy.analysis import Analysis
from vpy.display.ce3 import CE3 as Display
from vpy.todo import ToDo
from vpy.helper import init_customer_device

def main():
    io = Io()
    io.eval_args()
    ret = {"ok":True}
    result_type = "error"
    for id in io.ids:
        doc = io.get_doc_db(id)
        tdo = ToDo(doc)

        if tdo.type not in ["error", "srg_error"]:
            sys.exit("wrong script")
        if tdo.type == "error":
            result_type = "cont_expansion"
        if tdo.type == "srg_error":
            result_type = "srg_vg"

        display = Display(doc)
        cus_dev = init_customer_device(doc)
        analysis = doc.get("Calibration").get("Analysis")

        ## wrong type:
        del analysis["Values"]["Error"]

        ana = Analysis(doc, init_dict=analysis, analysis_type=result_type)
        res = Result(doc, result_type=result_type, skip=io.skip)

        ## conversion to ana.pressure_unit if necessary
        cal_dict = ana.pick_dict("Pressure", "cal")

        rstat_unit = cal_dict.get("Unit")

        if  rstat_unit != ana.pressure_unit:
            p_cal = ana.pick("Pressure", "cal", rstat_unit)
            p_ind_corr = ana.pick("Pressure", "ind_corr", rstat_unit)
            p_ind = ana.pick("Pressure", "ind", rstat_unit)
            p_ind_offset = ana.pick("Pressure", "ind_offset", rstat_unit)

            conv = ana.Const.get_conv(from_unit=rstat_unit, to_unit=ana.pressure_unit)

            p_cal = p_cal * conv
            p_ind = p_ind * conv
            p_ind_corr = p_ind_corr * conv
            p_ind_offset = p_ind_offset * conv

        else:
            p_cal = ana.pick("Pressure", "cal", ana.pressure_unit)
            p_ind_corr = ana.pick("Pressure", "ind_corr", ana.pressure_unit)
            p_ind = ana.pick("Pressure", "ind", ana.pressure_unit)
            p_ind_offset = ana.pick("Pressure", "offset", ana.pressure_unit)

        T_gas = ana.pick("Temperature", "Tuhv", "K")
        T_room = ana.pick("Temperature", "Troom", "K")
        if T_room is None:
            T_room = T_gas

        u_std = ana.pick("Uncertainty", "uncertPcal_rel" , "1")

        err = p_ind_corr/ p_cal - 1
        ana.store("Pressure", "cal", p_cal, ana.pressure_unit)
        ana.store("Pressure", "ind_corr", p_ind_corr, ana.pressure_unit)
        ana.store("Pressure", "ind", p_ind, ana.pressure_unit)
        ana.store("Pressure", "offset", p_ind_offset, ana.pressure_unit)
        ana.store("Pressure", "ind_offset", p_ind_offset, ana.pressure_unit)
        ana.store("Error", "ind", err, "1")
        ana.store("Uncertainty", "standard", u_std, "1")
        ana.store("Temperature", "gas", T_gas, "K")
        ana.store("Temperature", "room", T_room, "K")

        conv = ana.Const.get_conv(from_unit=ana.pressure_unit, to_unit=tdo.pressure_unit)
        average_index = tdo.make_average_index(p_cal*conv, tdo.pressure_unit, max_dev=0.2)

        ## will be filled up with aux values:
        d = {}

        display.check_outlier_err(ana)
        average_index, reject_index  = ana.ask_for_reject(average_index=average_index)
        flat_average_index = ana.flatten(average_index)

        if result_type == "cont_expansion":
            T, Tu = ana.ask_for_bake_out_temperature()
            if T is not None:
                d["Bakeout"] = True
                d["BakeoutTemperature"] = float(T)
                d["BakeoutTemperatureUnit"] = Tu
                t, tu = ana.ask_for_bake_out_time()
                d["BakeoutTime"] = float(t)
                d["BakeoutTimeUnit"] = tu
            else:
                d["Bakeout"] = False

            p, pu, t, tu = ana.ask_for_sputter()
            if t is not None:
                d["Sputter"] = True
                d["SputterPressure"] = float(p)
                d["SputterPressureUnit"] = pu
                d["SputterTime"] = float(t)
                d["SputterTimeUnit"] = tu
            else:
                d["Sputter"] = False

            d["Degas"] = ana.ask_for_degas()

        d["AverageIndex"] = average_index
        d["AverageIndexFlat"] = flat_average_index
        ana.store_dict(quant="AuxValues", d=d, dest=None)

        ## rm values
        p_cal = np.take(p_cal, flat_average_index)
        p_ind_corr = np.take(p_ind_corr, flat_average_index)
        err = np.take(err, flat_average_index)

        ## store reduced quant. for plot
        ana.store("Pressure", "red_ind_corr", p_ind_corr, ana.pressure_unit, dest="AuxValues")
        ana.store("Pressure", "red_cal", p_cal, ana.pressure_unit, dest="AuxValues")
        ana.store("Error", "red_ind", err, "1", dest="AuxValues")

        ## offset contrib
        cus_dev.offset_uncert(ana,  reject_index =  reject_index)

        ## default uncert. contrib.  repeat
        cus_dev.repeat_uncert(ana)
        cus_dev.digit_uncert(ana)
        cus_dev.device_uncert(ana)

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
        p_cal_mv, p_ind_mv, err_mv, u_mv = res.make_error_table(ana, pressure_unit=ana.pressure_unit, error_unit="1")

        ana.store("Pressure", "cal_mean", p_cal_mv, ana.pressure_unit , dest="AuxValues")
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
