import datetime
import time
import subprocess
import copy
import numpy as np
from .analysis import Analysis
from .todo import ToDo
from .values import Values, Date
from .constants import Constants


class Result(Analysis):
    """Holds a deep copy of ``document``. Container for storing
    Results of analysis.
    """
    head_cell = {
        "cal": "{\\(p_\\text{cal}\\)}",
        "ind": "{\\(p_\\text{ind}\\)}",
        "ind_corr": "{\\(p_\\text{ind} - p_\\text{offs}\\)}",
        "uncert_total_rel": "{\\(U(k=2)\\)}",
        "uncert_total_abs": "{\\(U(k=2)\\)}",
        "uncert_total_rel_cf": "{\\(U(CF)\\)}",
        "uncert_total_rel_e": "{\\(U(e)\\)}",
        "error":"{\\(e\\)}",
        "cf": "{\\(CF\\)}",
        "N":"{\\(N\\)}",
        "range":"range",
    }
    unit_cell = {
        "1": "",
        "mbar": "{(\\(\\si{\\mbar}\\))}",
        "Pa":"{(\\(\\si{\\pascal}\\))}",
        "%": "{(\\(\\si{\\percent}\\))}",
        "N":"",
        "range":"",
        }
    unit = {
        "mbar": "\\mbar",
        "Pa": "\\Pa"
        }
    gas = {
        "de": {
            "He": "Helium",
            "Ar": "Argon",
            "H2": "Wasserstoff",
            "N2": "Stickstoff",
            "Ne": "Neon"
            },
        "en": {
            "He":"helium",
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
        self.Date = Date(doc)
        self.lang = doc.get("Calibration",{}).get("Customer",{}).get("Lang", "en")
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

    def make_calibration_data_section(self, ana):
        """The Calibration data section should contain data valid
        for the entire calibration run
        """
        p_min, p_max, unit = self.ToDo.get_min_max_pressure()
        sec = { "PressureRangeBegin": p_min,
                "PressureRangeEnd": p_max,
                "PressureRangeUnit": unit,
        }
        self.store_dict(quant="CalibrationData", d=sec, dest=None, plain=True)

    def make_measurement_data_section(self, ana):
        """The measurement data section should contain data 
        valid for the measurement only
        """
        k = 2
        T_gas = ana.pick("Temperature", "after", "K")
        T_gas_mean = np.mean(T_gas)
        T_gas_unc = np.std(T_gas)*k
        T_gas_mean_str = self.Val.round_to_uncertainty(T_gas_mean, T_gas_unc, 2)
        T_gas_unc_str = self.Val.round_to_sig_dig(T_gas_unc, 2)

        T_room = ana.pick("Temperature", "room", "K")
        T_room_mean = np.mean(T_room)
        T_room_unc = np.std(T_room)*k
        T_room_mean_str = self.Val.round_to_uncertainty(T_room_mean, T_room_unc, 2)
        T_room_unc_str = self.Val.round_to_sig_dig(T_room_unc, 2)

        e_vis = ana.doc.get("AuxValues", {}).get("Evis")
        cf_vis = ana.doc.get("AuxValues", {}).get("CFvis")
        u_vis = ana.doc.get("AuxValues", {}).get("Uvis")
 
        gas = self.ToDo.get_gas()

        sec = { "GasTemperature": T_gas_mean_str,
                "GasTemperatureUncertainty": T_gas_unc_str,
                "MeasurementDate": self.Date.first_measurement(),
                "RoomTemperature": T_room_mean_str,
                "RoomTemperatureUncertainty": T_room_unc_str,
                "GasSpecies": self.gas[self.lang][gas],
                "Evis": self.Val.round_to_uncertainty(e_vis, u_vis, 2),
                "CFvis": self.Val.round_to_uncertainty(cf_vis, u_vis, 2),
        }
        self.store_dict(quant="MeasurementData", d=sec, dest=None, plain=True)

    def reduce_range_str(self, range_str,  average_index):
        return [range_str[v[0]] for v in average_index]


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
        u_std = ana.pick("Uncertainty", "standard", error_unit)

        av_idx = ana.doc["AuxValues"]["AverageIndex"]
        N = [len(i) for i in av_idx]

        range_str = ana.pick_dict("Range", "ind").get("Value")
      
        if range_str is not None:
            range_str = self.reduce_range_str(range_str=range_str, average_index=av_idx)
         

        cal = ana.reduce_by_average_index(value=cal, average_index=av_idx)

        ind = ana.reduce_by_average_index(value=ind, average_index=av_idx)
        error = ana.reduce_by_average_index(value=error, average_index=av_idx)
        cf = ana.reduce_by_average_index(value=cf, average_index=av_idx)
        u = ana.reduce_by_average_index(value=u, average_index=av_idx)
        u_std = ana.reduce_by_average_index(value=u_std, average_index=av_idx)

        cal_str = self.Val.round_to_uncertainty_array(cal, u_std*cal, 2, scientific=True)
        ind_str = self.Val.round_to_uncertainty_array(ind, u*cal, 2, scientific=True)        
        error_str = self.Val.round_to_uncertainty_array(error, u*k, 2)
        cf_str = self.Val.round_to_uncertainty_array(cf, u*k, 2)
          
        u_e_k2 = u*ind/cal*k
        u_e_k2_str = self.Val.round_to_sig_dig_array(u_e_k2, 2)
        
        u_cf_k2 = u*cal/ind*k
        u_cf_k2_str = self.Val.round_to_sig_dig_array(u_cf_k2, 2)

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
            "Type": "ind",
            "Unit": error_unit,
            "Value": error_str,
            "HeadCell": self.head_cell["error"],
            "UnitCell": self.unit_cell[error_unit]
            }
        cf_dict = {
            "Type": "ind",
            "Unit": error_unit,
            "Value": cf_str,
            "HeadCell": self.head_cell["cf"],
            "UnitCell": self.unit_cell[error_unit]
            }
        u_e_dict  = {
            "Type": "uncert_total_rel",
            "Unit": error_unit,
            "Value": u_e_k2_str,
            "HeadCell": self.head_cell["uncert_total_rel_e"],
            "UnitCell": self.unit_cell[error_unit]
            }
        u_cf_dict  = {
            "Type": "uncert_total_rel",
            "Unit": error_unit,
            "Value": u_cf_k2_str,
            "HeadCell": self.head_cell["uncert_total_rel_cf"],
            "UnitCell": self.unit_cell[error_unit]
            }
        n_dict = {
            "Type": "count",
            "Unit": "1",
            "Value": N,
            "HeadCell": self.head_cell["N"],
            "UnitCell": self.unit_cell["N"]
            }
        range_dict = {
            "Type": "ind",
            "Unit": "1",
            "Value": range_str,
            "HeadCell": self.head_cell["range"],
            "UnitCell": self.unit_cell["range"]
            } 
        self.store_dict(quant="Table", d=p_cal_dict, dest=None)
        self.store_dict(quant="Table", d=p_ind_corr_dict, dest=None)
        if add_n_column:
            self.store_dict(quant="Table", d=n_dict, dest=None)
        if range_str:
            self.store_dict(quant="Table", d=range_dict, dest=None)     
        self.store_dict(quant="Table", d=e_dict, dest=None)
        self.store_dict(quant="Table", d=cf_dict, dest=None)
        self.store_dict(quant="Table", d=u_e_dict, dest=None)
        self.store_dict(quant="Table", d=u_cf_dict, dest=None)

        self.log.info("Result error table written")

        return ind, error, u

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

