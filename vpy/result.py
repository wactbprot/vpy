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
        "ind_corr": "{\\(p_\\text{ind} - p_\\text{r}\\)}",
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
    unit_trans = {
        "mbar": "\\mbar",
        "Pa": "\\Pa"
        }

    ## wrong position for that kind of info
    ## 
    #gas = {
    #    "de": {
    #        "He": "Helium",
    #        "Ar": "Argon",
    #        "H2": "Wasserstoff",
    #        "N2": "Stickstoff",
    #        "Ne": "Neon"
    #        },
    #    "en": {
    #        "He": "helium",
    #        "Ar": "argon",
    #        "H2": "hydrogen",
    #        "N2": "nitrogen",
    #        "Ne": "neon"
    #        }
    #    }

    def __init__(self, doc, result_type="expansion", skip=False):

        
        init_dict = {"Skip":skip,
                    "Date": [{
                    "Type": "generated",
                    "Value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}],
                    "AuxValues":{
                        "AnalysisProgram": "vpy"
                    },
                    "ResultType": result_type
             }

        self.ToDo = ToDo(doc)
        self.Const = Constants(doc)
        self.Val = Values(doc)
        self.Date = Date(doc)
        self.lang = doc.get("Calibration",{}).get("Customer",{}).get("Lang", "en")
        self.org = copy.deepcopy(doc)
       
        super().__init__(doc, init_dict)

    ## (vpy) bock04@i75464:~/vpy$ grep -r gatherby .
    ##     ./vpy/result.py:    def gatherby_idx(self, l, compare_function):
    ##     ./jupyter_utils.py:def gatherby_idx(l, compare_function):
    ##
    ## --> shipped function to values.py

    def make_calibration_data_section(self, ana):
        """The Calibration data section should contain data valid
        for the entire calibration run.

        The former p_min, p_max values generated here belong to the
        measurement (expanstion, direct measurement).
        """
        pass

    def gen_temperature_gas_entry(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "gas", unit)
        t_mean = np.mean(t)
        t_unc = np.std(t)*k

        sec["GasTemperature"] = self.Val.round_to_uncertainty(t_mean, t_unc, 2)
        sec["GasTemperatureUncertainty"] = self.Val.round_to_sig_dig(t_unc, 2)    
        sec["GasTemperatureUnit"] = unit

        return sec        

    def gen_temperature_gas_entry_se2(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "gas", unit)
        t = [i for i in t if i>274]
        t_mean = np.mean(t)
        t_unc = np.std(t)*k

        sec["GasTemperature"] = self.Val.round_to_uncertainty(t_mean, t_unc, 2)
        sec["GasTemperatureUncertainty"] = self.Val.round_to_sig_dig(t_unc, 2)    
        sec["GasTemperatureUnit"] = unit
        
        return sec
    
    def gen_temperature_room_entry(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "room", unit)
        t_mean = np.mean(t)
        t_unc = np.std(t)*k
        sec["RoomTemperature"] = self.Val.round_to_uncertainty(t_mean, t_unc, 1)
        sec["RoomTemperatureUncertainty"] = self.Val.round_to_sig_dig(t_unc, 1)
        sec["RoomTemperatureUnit"] = unit

        return sec
    
    def gen_temperature_estimated_entry(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "frs5", "C")
        t_mean = np.mean(t) - 4. + 273.15
        t_unc = 0.5
        sec["EstimatedTemperature"] = self.Val.round_to_uncertainty(t_mean, t_unc, 1)
        sec["EstimatedTemperatureUncertainty"] = self.Val.round_to_sig_dig(t_unc, 1)
        sec["EstimatedTemperatureUnit"] = unit

        return sec

    def gen_temperature_correction(self, ana, sec):

        p_tdo, p_tdo_unit = self.ToDo.Pres.get_value_and_unit("target")
        conv = self.Const.get_conv(from_unit=p_tdo_unit, to_unit="Pa")

        p_tdo = conv * p_tdo
        p_tdo_evis = [p_tdo[i] for i in range(len(p_tdo)) if p_tdo[i] < 95]

        if len(p_tdo_evis) > 1:
            sec["TemperatureCorrection"] = "yes"
        else:
            sec["TemperatureCorrection"] ="no"

        return sec

    def gen_meas_date_entry(self, ana, sec):

        sec["MeasurementDate"] = self.Date.first_measurement()
        
        return sec 
    
    def gen_min_max_entry(self, ana, sec, unit="Pa"):

        p_min, p_max, todo_unit = self.ToDo.get_min_max_pressure()
        conv = float(self.Const.get_conv(from_unit=todo_unit, to_unit=unit))
        sec["PressureRangeBegin"] = "{:.1e}".format(p_min*conv)
        sec["PressureRangeEnd"] = "{:.1e}".format(p_max*conv)
        sec["PressureRangeUnit"] = self.unit_trans[unit]
        
        return sec

    def gen_min_max_entry_direct_se2(self, ana, sec, unit="Pa"):

        ex = ana.org["Calibration"]["Measurement"]["Values"]["Expansion"]["Value"]
        av_idx = ana.doc["AuxValues"]["AverageIndexFlat"]
        p_cal = ana.pick("Pressure", "cal", "Pa")

        p_cal = [p_cal[i] for i in av_idx if ex[i]=="direkt"]

        if len(p_cal)>0:
            sec["PressureRangeDirectBegin"] = "{:.1e}".format(min(p_cal))
            sec["PressureRangeDirectEnd"] = "{:.1e}".format(max(p_cal))
        
        return sec        

    def extr_val(self, x):
        if type(x) is list:
            return x[0]
        else:
            return x
       
    
    def gen_cdg_entry(self, ana, sec):
        e_vis = self.extr_val(self.doc.get("AuxValues", {}).get("Evis"))
        u_vis = self.extr_val(self.doc.get("AuxValues", {}).get("Uvis"))
        cf_vis = self.extr_val(self.doc.get("AuxValues", {}).get("CFvis"))

        if e_vis and u_vis:
            sec["Evis"] = self.Val.round_to_uncertainty(e_vis, u_vis, 2)
            sec["UncertEvis"] = self.Val.round_to_uncertainty(e_vis*u_vis, u_vis, 2)
            
        
        if cf_vis and u_vis:
            sec["CFvis"] = self.Val.round_to_uncertainty(cf_vis, u_vis, 2)
            sec["UncertCFvis"] = self.Val.round_to_uncertainty(cf_vis*u_vis, u_vis, 2)
        
        return sec
    
    def gen_uncert_offset_entry(self, ana, sec):
        uncert_contribs = ana.doc.get("AuxValues", {}).get("OffsetUncertContrib")
        if uncert_contribs and "Unit" in uncert_contribs:
            if uncert_contribs["Unit"] is not "Pa":
                sys.exit("Expect Pa as offset uncert contrib unit")
            else:
                unit = "\\pascal"
            entr = {}
            for cont in uncert_contribs:
                if cont is not "Unit":
                    value =  "{:.1E}".format(uncert_contribs[cont])
                    entr[cont] = "\\SI{"+value+"}{"+unit+"}"

            sec["OffsetUncertContrib"] = entr

        return sec  

    def gen_srg_entry(self, ana, sec):
        """
            ..todo::

                s. issue https://a75436.berlin.ptb.de/vaclab/vpy/issues/15
        """
        
        sigma_null = self.doc.get("AuxValues", {}).get("SigmaNull")
        sigma_slope = self.doc.get("AuxValues", {}).get("SigmaCorrSlope")
        sigma_std = self.doc.get("AuxValues", {}).get("SigmaStd")
        
        if sigma_null and sigma_slope and sigma_std:
            sec["SigmaNull"] = self.Val.round_to_uncertainty(sigma_null[0], 2e-3, 2)
            sec["SigmaCorrSlope"] = self.Val.round_to_uncertainty(sigma_slope[0], 2e-3, 2)
            sec["SigmaStd"] = self.Val.round_to_uncertainty(sigma_std[0], 2e-3, 2)
            sec["OffsetMean"] = "{:.4E}".format(self.doc.get("AuxValues", {}).get("OffsetMean")[0])
            sec["OffsetStd"] = "{:.1E}".format(self.doc.get("AuxValues", {}).get("OffsetStd")[0])
            sec["OffsetUnit"] = self.doc.get("AuxValues", {}).get("OffsetUnit")
       
        return sec

    def make_measurement_data_section(self, ana, k=2, result_type="expansion", pressure_unit="Pa"):
        """The measurement data section should contain data 
        belonging to one measurement (gas species, expansion or direct comp. etc) only. 
        """
        sec = {}
        if result_type == "expansion":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_temperature_correction(ana, sec)
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)

        if result_type == "se2_expansion":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_temperature_correction(ana, sec)            
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)

        if result_type == "se2_direct":
            sec = self.gen_temperature_room_entry(ana, sec)    
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)  

        if result_type == "se2_expansion_direct":
            sec = self.gen_temperature_gas_entry_se2(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_temperature_correction(ana, sec)            
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_min_max_entry_direct_se2(ana, sec)            
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)  

        if result_type == "direct":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_min_max_entry(ana, sec)
            
        if result_type == "pressure_balance":
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_temperature_estimated_entry(ana, sec)

        if result_type == "rotary_piston_gauge":
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_min_max_entry(ana, sec)

        sec = self.gen_uncert_offset_entry(ana, sec)
        
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
        ind = self.get_reduced_pressure_ind(ana, av_idx, pressure_unit)
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
        ind = np.array(ind_dict.get("Value"), dtype=np.float)  * ind_conv 
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
        range_dict = ana.pick_dict("Range", "ind")
        
        if range_dict is not None:
            range_str = range_dict.get("Value")
            return [range_str[v[0]] for v in av_idx]
        else:
            return None

    def make_error_table(self, ana, pressure_unit='mbar', error_unit='%', add_n_column=False):
        
        av_idx = self.doc["AuxValues"]["AverageIndex"]
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
