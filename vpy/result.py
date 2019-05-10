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
    
    dcc_unit = {
        "1":"\\one",
        "mbar": "\\hecto\\kilogram\\metre\\tothe{-1}\\second\\tothe{-2}",
        "Pa":"\\kilogram\\metre\\tothe{-1}\\second\\tothe{-2}",
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
            "He": "helium",
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
        for the entire calibration run.

        The former p_min, p_max values generated here belong to the
        measurement (expanstion, direct measurement).
        """
        pass

    def make_measurement_data_section(self, ana, k=2):
        """The measurement data section should contain data 
        valid for the measurement only
        """

        T_gas = ana.pick("Temperature", "gas", "K")
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
        p_min, p_max, unit = self.ToDo.get_min_max_pressure()
        
        sec = {
            "PressureRangeBegin": p_min,
            "PressureRangeEnd": p_max,
            "PressureRangeUnit": unit,
            "GasTemperature": T_gas_mean_str,
            "GasTemperatureUncertainty": T_gas_unc_str,
            "MeasurementDate": self.Date.first_measurement(),
            "RoomTemperature": T_room_mean_str,
            "RoomTemperatureUncertainty": T_room_unc_str,
            "GasSpecies": self.gas[self.lang][gas],
            "Evis": self.Val.round_to_uncertainty(e_vis, u_vis, 2),
            "CFvis": self.Val.round_to_uncertainty(cf_vis, u_vis, 2),
        }
        self.store_dict(quant="MeasurementData", d=sec, dest=None, plain=True)

    def make_cal_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        cal = self.get_reduced_pressure_cal(ana, av_idx, pressure_unit)
        u_std = self.get_reduced_uncert_std(ana, av_idx, error_unit)
        cal_str = self.Val.round_to_uncertainty_array(cal, u_std*cal, 2, scientific=True)

        return cal_str

    def make_ind_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        ind = self.get_reduced_pressure_ind(ana, av_idx, pressure_unit)
        u_total = self.get_reduced_uncert_total(ana, av_idx, error_unit)
        ind_str = self.Val.round_to_uncertainty_array(ind, u_total*ind, 2, scientific=True)

        return ind_str

    def make_error_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        error = self.get_reduced_error(ana, av_idx, error_unit)
        u_total = self.get_reduced_uncert_total(ana, av_idx, error_unit)
        error_str = self.Val.round_to_uncertainty_array(error, u_total*k, 2)

        return error_str
    
    def make_cf_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        cf = self.get_reduced_cf(ana, av_idx, error_unit)
        u_total = self.get_reduced_uncert_total(ana, av_idx, error_unit)
        cf_str = self.Val.round_to_uncertainty_array(cf, u_total*k, 2)

        return cf_str

    def make_uncert_cal_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        cal = self.get_reduced_pressure_cal(ana, av_idx, pressure_unit)
        u_std = self.get_reduced_uncert_std(ana, av_idx, error_unit)

        u_std_k2 = u_std*cal*k #pressure_unit
        u_std_k2_str = self.Val.round_to_sig_dig_array(u_std_k2, 2)

        return  u_std_k2_str     

    def make_uncert_ind_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        ind = self.get_reduced_pressure_ind (ana, av_idx, pressure_unit)
        u_dev = self.get_reduced_uncert_dev(ana, av_idx, error_unit)

        u_dev_k2 = u_dev*ind*k #pressure_unit
        u_dev_k2_str = self.Val.round_to_sig_dig_array(u_dev_k2, 2)

        return  u_dev_k2_str     

    def make_uncert_error_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):      
        ind = self.get_reduced_pressure_ind(ana, av_idx, pressure_unit)
        cal = self.get_reduced_pressure_cal(ana, av_idx, pressure_unit)
        u_total = self.get_reduced_uncert_total(ana, av_idx, error_unit)

        u_e_k2 = u_total*ind/cal*k
        u_e_k2_str = self.Val.round_to_sig_dig_array(u_e_k2, 2)

        return  u_e_k2_str     

    def make_uncert_cf_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        ind = self.get_reduced_pressure_ind(ana, av_idx, pressure_unit)
        cal = self.get_reduced_pressure_cal(ana, av_idx, pressure_unit)
        u_total = self.get_reduced_uncert_total(ana, av_idx, error_unit)
        
        u_cf_k2 = u_total*cal/ind*k
        u_cf_k2_str = self.Val.round_to_sig_dig_array(u_cf_k2, 2)

        return  u_cf_k2_str   

    def get_reduced_pressure_ind(self, ana, av_idx, unit):
        ind_dict = ana.pick_dict("Pressure", "ind_corr")
        ind_conv = self.Const.get_conv(from_unit=ind_dict.get("Unit"), to_unit=unit)
        ind = ind_dict.get("Value") * ind_conv 
        ind = ana.reduce_by_average_index(value=ind, average_index=av_idx)
        
        return ind

    def get_reduced_pressure_cal(self, ana, av_idx, unit):
        cal_dict = ana.pick_dict("Pressure", "cal") 
        cal_conv = self.Const.get_conv(from_unit=cal_dict.get("Unit"), to_unit=unit)
        cal = cal_dict.get("Value") * cal_conv 
        cal = ana.reduce_by_average_index(value=cal, average_index=av_idx)
        return cal

    def get_reduced_uncert_total(self, ana, av_idx, unit):
        u_total = ana.pick("Uncertainty", "total_rel", unit)
        u_total = ana.reduce_by_average_index(value=u_total, average_index=av_idx)

        return u_total

    def get_reduced_uncert_std(self, ana, av_idx, unit):
        u_std = ana.pick("Uncertainty", "standard", unit)
        u_std = ana.reduce_by_average_index(value=u_std, average_index=av_idx)
        
        return u_std
    
    def get_reduced_uncert_dev(self, ana, av_idx, unit):
        u_dev = ana.pick("Uncertainty", "device", unit)
        u_dev = ana.reduce_by_average_index(value=u_dev, average_index=av_idx)
        
        return u_dev

    def get_reduced_error(self, ana, av_idx, unit):
        error = ana.pick("Error", "ind", unit)
        error = ana.reduce_by_average_index(value=error, average_index=av_idx)
        
        return error

    def get_reduced_cf(self, ana, av_idx, unit):
        error = ana.pick("Error", "ind", unit)
        if unit == "%":
            cf = 1.0/(error/100.0 +1.0)
        if unit == "1":
            cf = 1.0/(error +1.0)

        cf = ana.reduce_by_average_index(value=cf, average_index=av_idx)

        return cf

    def get_reduced_range_str(self, ana, av_idx):
        range_str = ana.pick_dict("Range", "ind").get("Value")
        if range_str is not None:
            return [range_str[v[0]] for v in av_idx]

    def make_error_table(self, ana, pressure_unit='mbar', error_unit='%', add_n_column=False):
        av_idx = ana.doc["AuxValues"]["AverageIndex"]
        k = 2
        prob = 0.95
        cal_str = self.make_cal_entry(ana, av_idx, pressure_unit, error_unit)

        ind_str = self.make_ind_entry(ana, av_idx, pressure_unit, error_unit)
        error_str = self.make_error_entry(ana, av_idx, pressure_unit, error_unit)
        cf_str = self.make_cf_entry(ana, av_idx, pressure_unit, error_unit)
        u_e_k2_str = self.make_uncert_error_entry(ana, av_idx, pressure_unit, error_unit)
        u_cf_k2_str = self.make_uncert_cf_entry(ana, av_idx, pressure_unit, error_unit)
        u_cal_k2_str = self.make_uncert_cal_entry(ana, av_idx, pressure_unit, error_unit)

        u_ind_k2_str = self.make_uncert_ind_entry(ana, av_idx, pressure_unit, error_unit)

        range_str = self.get_reduced_range_str(ana, av_idx)

        self.store_dict(quant="Table", d = {"Type": "cal",
                                            "DCCOut": True,
                                            "CoverageFactor": k,
                                            "CoverageProbability":prob,
                                            "Quantity": "Pressure",
                                            "Name": "calibration pressure",
                                            "Uncertainty": u_cal_k2_str,
                                            "DCCUnit": self.dcc_unit[pressure_unit],
                                            "Unit": pressure_unit,
                                            "Value": cal_str,
                                            "HeadCell": self.head_cell["cal"],
                                            "UnitCell": self.unit_cell[pressure_unit]}, dest=None)
        
        self.store_dict(quant="Table", d = {"Type": "ind_corr",
                                            "DCCOut": True,
                                            "CoverageFactor": k,
                                            "CoverageProbability":prob,
                                            "Quantity": "Pressure",
                                            "Name": "offset corrected indicated pressure",
                                            "Uncertainty": u_ind_k2_str,
                                            "DCCUnit": self.dcc_unit[pressure_unit],
                                            "Unit": pressure_unit,
                                            "Value": ind_str,
                                            "HeadCell": self.head_cell["ind_corr"],
                                            "UnitCell": self.unit_cell[pressure_unit]}, dest=None)

        self.store_dict(quant="Table", d = {"Type": "ind",
                                            "DCCOut": True,
                                            "CoverageFactor": k,
                                            "CoverageProbability":prob,
                                            "Quantity": "Error",
                                            "Name": "relative error of indication",
                                            "Uncertainty": u_e_k2_str,
                                            "DCCUnit": self.dcc_unit[error_unit],
                                            "Unit": error_unit,
                                            "Value": error_str,
                                            "HeadCell": self.head_cell["error"],
                                            "UnitCell": self.unit_cell[error_unit]}, dest=None)

        self.store_dict(quant="Table", d = {"Type": "ind",
                                            "DCCOut": True,
                                            "CoverageFactor": k,
                                            "CoverageProbability":prob,
                                            "Quantity": "Correction",
                                            "Name": "correction factor",
                                            "Uncertainty": u_cf_k2_str,
                                            "DCCUnit": self.dcc_unit["1"],
                                            "Unit": error_unit,
                                            "Value": cf_str,
                                            "HeadCell": self.head_cell["cf"],
                                            "UnitCell": self.unit_cell[error_unit]}, dest=None)
          
        self.store_dict(quant="Table", d = {"Type": "uncert_total_rel",
                                            "DCCOut": False,
                                            "Unit": error_unit,
                                            "Value": u_e_k2_str,
                                            "HeadCell": self.head_cell["uncert_total_rel_e"],
                                            "UnitCell": self.unit_cell[error_unit]}, dest=None)

        self.store_dict(quant="Table", d = {"Type": "uncert_total_rel",
                                            "DCCOut": False,
                                            "Unit": error_unit,
                                            "Value": u_cf_k2_str,
                                            "HeadCell": self.head_cell["uncert_total_rel_cf"],
                                            "UnitCell": self.unit_cell[error_unit]
                                            }, dest=None)
        if add_n_column:
            self.store_dict(quant="Table", d = {"Type": "count",
                                                "Unit": "1",
                                                "Value": [len(i) for i in av_idx],
                                                "HeadCell": self.head_cell["N"],
                                                "UnitCell": self.unit_cell["N"]
                                                }, dest=None)
       
        if range_str is not None:
            self.store_dict(quant="Table", d = {"Type": "ind",
                                                "Unit": "1",
                                                "Value": range_str,
                                                "HeadCell": self.head_cell["range"],
                                                "UnitCell": self.unit_cell["range"]}, dest=None) 
    
        self.log.info("Result error table written")

        ind = self.get_reduced_pressure_ind(ana, av_idx, pressure_unit)
        error = self.get_reduced_error(ana, av_idx, error_unit)
        u = self.get_reduced_uncert_total(ana, av_idx, error_unit)
        
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

