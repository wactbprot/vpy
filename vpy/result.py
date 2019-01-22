import datetime
import time
import subprocess
import copy
import numpy as np
from .analysis import Analysis
from .todo import ToDo
from .values import Values
from .constants import Constants


class Result(Analysis):
    """Holds a deep copy of ``document``. Container for storing
    Results of analysis.
    """
    head_cell = {
        "cal": "{\\(p_\\text{cal}\\)}",
        "ind": "{\\(p_\\text{ind}\\)}",
        "ind_corr": "{\\(p_\\text{ind} - p_\\text{r}\\)}",
        "uncertTotal_rel": "{\\(U(k=2)\\)}",
        "uncertTotal_abs": "{\\(U(k=2)\\)}",
        "error":"{\\(e\\)}",
        "cf": "{\\(CF\\)}",
        "N":"{\\(N\\)}",
    }
    unit_cell = {
        "1": "",
        "mbar": "mbar",
        "Pa":"Pa",
        "%": "{\\(\\si{\\percent}\\)}",
        "N":"",
        }
    unit = {
        "mbar": "\\mbar",
        "Pa": "\\Pa"
        }
    gas = {
        "de": {
            "Ar": "Argon",
            "H2": "Wasserstoff",
            "N2": "Stickstoff",
            "Ne": "Neon"
            },
        "en": {
            "Ar": "argon",
            "H2": "hydrogen",
            "N2": "nitrogen",
            "Ne": "neon"
            }
        }

    def __init__(self, doc):

        d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        init_dict = {"Date": [{
                    "Type": "generated",
                    "Value": d}]
             }

        self.ToDo = ToDo(doc)
        self.Const = Constants(doc)
        self.Val = Values(doc)
        self.org = copy.deepcopy(doc)
        super().__init__(doc, init_dict)


    def gatherby_idx(self, l, compare_function):
        groups = {}
        for i in range(len(l)):
            for j in groups:
                if compare_function(l[i], l[j]):
                    groups[j].append(i)
                    break
            else: groups[i] = [i]
        return list(groups.values())

    def make_error_table(self, ana, pressure_unit='mbar', error_unit='%', add_n_column=False):
        k=2

        cal_dict = ana.pick_dict("Pressure", "cal")
        cal_conv = self.Const.get_conv(from_unit=cal_dict.get("Unit"), to_unit=pressure_unit)
        cal = cal_conv * cal_dict.get("Value")

        ind_dict = ana.pick_dict("Pressure", "ind_corr")
        ind_conv = self.Const.get_conv(from_unit=ind_dict.get("Unit"), to_unit=pressure_unit)
        ind = ind_conv * ind_dict.get("Value")

        cf = cal/ind
        error = ana.pick("Error", "ind", error_unit)
        u = ana.pick("Uncertainty", "total_rel", error_unit)
        
        av_idx = ana.doc["AuxValues"]["AverageIndex"]
        N = [len(i) for i in av_idx]
        cal = ana.reduce_by_average_index(value=cal, average_index=av_idx)

        ind = ana.reduce_by_average_index(value=ind, average_index=av_idx)
        error = ana.reduce_by_average_index(value=error, average_index=av_idx)
        cf = ana.reduce_by_average_index(value=cf, average_index=av_idx)
        u = ana.reduce_by_average_index(value=u, average_index=av_idx)

        #format output
        cal_str = [f"{i:.4e}" for i in cal]
        ind_str = [f"{i:.4e}" for i in ind]
        error_str = self.Val.round_to_uncertainty_array(error, u*k, 2)
        cf_str = self.Val.round_to_uncertainty_array(cf, u*k, 2)
        u_k2_str = self.Val.round_to_sig_dig_array(u*k, 2)

        p_cal_dict = {
            "Type": "cal",
            "Unit": pressure_unit,
            "Value": cal_str,
            "HeadCell": self.head_cell["cal"],
            "UnitCell": self.unit_cell[pressure_unit]
            }
        p_ind_corr_dict = {
            "Type": "ind_corr",
            "Unit": pressure_unit,
            "Value": ind_str,
            "HeadCell": self.head_cell["ind_corr"],
            "UnitCell": self.unit_cell[pressure_unit]
            }
        e_dict = {
            "Type": "relative",
            "Unit": error_unit,
            "Value": error_str,
            "HeadCell": self.head_cell["error"],
            "UnitCell": self.unit_cell[error_unit]
            }
        cf_dict = {
            "Type": "relative",
            "Unit": error_unit,
            "Value": cf_str,
            "HeadCell": self.head_cell["cf"],
            "UnitCell": self.unit_cell[error_unit]
            }
        u_dict  = {
            "Type": "uncertTotal_rel",
            "Unit": error_unit,
            "Value": u_k2_str,
            "HeadCell": self.head_cell["uncertTotal_rel"],
            "UnitCell": self.unit_cell[error_unit]
            }
        n_dict = {
            "Type": "count",
            "Unit": "1",
            "Value": N,
            "HeadCell": self.head_cell["N"],
            "UnitCell": self.unit_cell["N"]
            }
        self.store_dict(quant="Table", d=p_cal_dict, dest=None)
        self.store_dict(quant="Table", d=p_ind_corr_dict, dest=None)
        if add_n_column:
            self.store_dict(quant="Table", d=n_dict, dest=None)        
        self.store_dict(quant="Table", d=e_dict, dest=None)
        self.store_dict(quant="Table", d=cf_dict, dest=None)
        self.store_dict(quant="Table", d=u_dict, dest=None)

        self.log.info("Result error table written")


    def make_formula_section(self, ana):

        T_after = ana.pick("Temperature", "after", "C")
        T_room = ana.pick("Temperature", "room", "C")
        mdate = ana.get_object("Type","measurement")["Value"]

        mm_idx = ana.doc["AuxValues"]["MainMaesurementIndex"]

        av_idx = ana.doc["AuxValues"]["AverageIndex"]
        offset_unc = ana.pick("Uncertainty", "offset", "mbar")

        offset_uncertainty = np.asarray([np.mean(np.take(offset_unc, i)) for i in av_idx])
        
        mdate = np.take(mdate, mm_idx)[0]

        T_after = np.take(T_after, mm_idx)
        T_after_mean = np.mean(T_after)
        T_after_unc = np.std(T_after)
        T_after_mean_str = self.Val.round_to_uncertainty(T_after_mean, T_after_unc, 2)
        T_after_unc_str = self.Val.round_to_sig_dig(T_after_unc, 2)
        T_after_mean_K_str = self.Val.round_to_uncertainty(T_after_mean + 273.15, T_after_unc, 2)

        T_room = np.take(T_room, mm_idx)
        T_room_mean = np.mean(T_room)
        T_room_unc = np.std(T_room)
        T_room_mean_str = self.Val.round_to_uncertainty(T_room_mean, T_room_unc, 2)
        T_room_unc_str = self.Val.round_to_sig_dig(T_room_unc, 2)

        zero_stability_str = self.Val.round_to_sig_dig(min(offset_uncertainty), 2)

        target = self.org["Calibration"]["ToDo"]["Values"]["Pressure"]["Value"]
        target_unit = self.org["Calibration"]["ToDo"]["Values"]["Pressure"]["Unit"]
        target_unit = self.unit[target_unit]
        gas = self.org["Calibration"]["ToDo"]["Gas"]
        language = self.org["Calibration"]["Customer"]["Lang"]
        gas = self.gas[language][gas]
        print("#")
        form = {
            "GasTemperature": T_after_mean_str,
            "GasTemperatureUncertainty": T_after_unc_str,
            "MeasurementDate": mdate,
            "PressureRangeBegin": target[0],
            "PressureRangeEnd": target[-1],
            "PressureRangeUnit": target_unit,
            "GasSpecies": gas,
            "RoomTemperature": T_room_mean_str,
            "RoomTemperatureUncertainty": T_room_unc_str,
            "ZeroStability": zero_stability_str,
            "ZeroStabilityUnit": target_unit,
            "Evis": ana.get_value("Error", "evis", "%"),
            "GasTemperatureEvis": T_after_mean_K_str,
            "GasTemperatureEvisUncertainty": T_after_unc_str
            }
        print("#")
        self.store_dict(quant="Formula", d=form, dest=None, plain=True)

        self.log.info("Formula section written")

        self.log.info("AuxValues section written")

