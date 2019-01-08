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
    }
    unit_cell = {
        "1": "",
        "mbar": "mbar",
        "%": "{\\(\\si{\\percent}\\)}"
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


    def u_PTB_rel(self, p_list):
        return np.asarray([np.piecewise(p, [p <= 0.00027, p <= 0.003, p <= 0.0073, p <= 0.09, p <= 10, p <= 80,  80 < p],
                                        [0.0014, 0.001, 0.00092, 0.00086, 0.00075, 0.00019, 0.00014]).tolist() for p in p_list])

    def repeat_rel(self, p_list):
        return np.asarray([np.piecewise(p, [p <= 0.1, p <= 9.5, p > 9.5], [0.0008, 0.0003, 0.0001]).tolist() for p in p_list])


    def make_error_table(self, ana):

        cal = ana.pick("Pressure", "cal", "mbar")
        ind = ana.pick("Pressure", "ind", "mbar")
        error = 100 * (ind - cal) / cal

        av_idx = ana.doc["AuxValues"]["AverageIndex"]
        offset_unc = ana.pick("Uncertainty", "offset", "mbar")

        offset_uncertainty = np.asarray([np.mean(np.take(offset_unc, i)) for i in av_idx])

        n_avr = np.asarray([len(i) for i in av_idx])
        cal = self.cal = np.asarray([np.mean(np.take(cal, i)) for i in av_idx])
        ind = self.ind = np.asarray([np.mean(np.take(ind, i)) for i in av_idx])
        error = self.error = np.asarray([np.mean(np.take(error, i)) for i in av_idx])

        # digitizing error still missing
        u_ind_abs = np.sqrt((cal * self.repeat_rel(cal))**2 + offset_uncertainty**2)
        k2 = self.k2 = 2 * 100 * ind / cal * np.sqrt((u_ind_abs / ind)**2 + self.u_PTB_rel(cal)**2)

        #format output
        cal_str = [f"{i:.4e}" for i in cal]
        ind_str = [f"{i:.4e}" for i in ind]
        error_str = self.Val.round_to_uncertainty_array(error, k2, 2)
        k2_str = self.Val.round_to_sig_dig_array(k2, 2)

        p_cal = {
            "Type": "cal",
            "Unit": "mbar",
            "Value": cal_str,
            "HeadCell": self.head_cell["cal"],
            "UnitCell": self.unit_cell["mbar"]
            }
        p_ind_corr = {
            "Type": "ind_corr",
            "Unit": "mbar",
            "Value": ind_str,
            "HeadCell": self.head_cell["ind_corr"],
            "UnitCell": self.unit_cell["mbar"]
            }
        e = {
            "Type": "relative",
            "Unit": "%",
            "Value": error_str,
            "HeadCell": self.head_cell["error"],
            "UnitCell": self.unit_cell["%"]
            }
        u  = {
            "Type": "uncertTotal_rel",
            "Unit": "%",
            "Value": k2_str,
            "HeadCell": self.head_cell["uncertTotal_rel"],
            "UnitCell": self.unit_cell["%"]
            }

        self.store_dict(quant="Table", d=p_cal, dest=None)
        self.store_dict(quant="Table", d=p_ind_corr, dest=None)
        self.store_dict(quant="Table", d=e, dest=None)
        self.store_dict(quant="Table", d=u, dest=None)

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

