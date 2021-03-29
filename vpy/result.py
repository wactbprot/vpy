import datetime
import time
import subprocess
import copy
import numpy as np
import sys
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
        "offset": "{\\(p_\\text{ind,r}\\)}",
        "ind_corr": "{\\(p_\\text{ind} - p_\\text{ind,r}\\)}",
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
        "mbar": "{in \\(\\si{\\mbar}\\)}",
        "Pa":"{in \\(\\si{\\pascal}\\)}",
        "%": "{in \\(\\si{\\percent}\\)}",
        "N":"",
        "range":"",
        }

    dcc_unit = {
        "1":"\\one",
        "mbar": "\\hecto\\kilogram\\metre\\tothe{-1}\\second\\tothe{-2}",
        "Pa":"\\kilogram\\metre\\tothe{-1}\\second\\tothe{-2}",
        }
    unit_trans = {
        "h":"\\hour",
        "mbar": "\\millibar",
        "Pa": "\\pascal",
        "1/Pa": "\\per\\pascal",
        "K": "\\kelvin",
        "C":"\\degreeCelsius",
        "DCR":"\\per\\second",
        "none":""
        }
    k_trans = {1:0.68,
               2:0.95,
               3:1,}

    def __init__(self, doc, result_type="expansion", skip=False, with_values_section=False):

        init_dict = {"Skip":skip,
                    "Date": [{
                    "Type": "generated",
                    "Value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}],
                    "AuxValues":{
                        "AnalysisProgram": "vpy"
                    },
                    "ResultType": result_type
             }
        if with_values_section:
             init_dict["Values"] = {}

        self.ToDo = ToDo(doc)
        self.Const = Constants(doc)
        self.Val = Values(doc)
        self.Date = Date(doc)
        self.lang = doc.get("Calibration",{}).get("Customer",{}).get("Lang", "en")
        self.org = copy.deepcopy(doc)

        super().__init__(doc, init_dict)

    def to_si_expr(self, v, unit):
        return "\\SI{"+ str(v) + "}{" + self.unit_trans[unit] + "}"

    def to_si_pm_expr(self, v, u, unit):
        return self.to_si_expr("" + str(v) + "+-" + str(u), unit)

    def gen_temperature_gas_entry(self, ana, sec, unit="K", k=2):
        """Temperature of measurement gas. Type B uncertainty: section 5.3.5 MUB
        http://a73435.berlin.ptb.de:82/lab/tree/QS/QSE-SE3-20-2-se3_mub.ipynb
        """


        t = ana.pick("Temperature", "gas", unit)

        av_idx = ana.doc["AuxValues"]["AverageIndexFlat"]
        t = np.take(t,av_idx)
        t_mean = np.mean(t)

        u_b = 0.03 #K
        t_unc =np.sqrt(np.power(u_b,2)+ np.power(np.std(t),2))*k

        v = self.Val.round_to_uncertainty(t_mean, t_unc, 2)
        u = self.Val.round_to_sig_dig(t_unc, 2)

        d={}
        d["TemperatureGas"] = float(v)
        d["TemperatureGasUnit"] = "K"
        d["TemperatureGasUncertainty"] = float(u)
        d["TemperatureGasCoverageFactor"] = k
        d["TemperatureGasProb"] = self.k_trans[k]
        ana.store_dict(quant='AuxValues', d=d, dest=None)

        sec["GasTemperature"] = self.to_si_pm_expr(v, u, unit)

        return sec

    def gen_temperature_gas_entry_se2(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "gas", unit)
        t = [i for i in t if i>274]
        t_mean = np.mean(t)
        t_unc = np.std(t)*k

        v = self.Val.round_to_uncertainty(t_mean, t_unc, 2)
        u = self.Val.round_to_sig_dig(t_unc, 2)

        sec["GasTemperature"] = self.to_si_pm_expr(v, u, unit)

        return sec

    def gen_temperature_room_entry(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "room", unit)
        av_idx = ana.doc["AuxValues"]["AverageIndexFlat"]
        t = np.take(t,av_idx)
        t_mean = np.mean(t)
        t_unc = 0.1 #np.std(t)*k

        v = self.Val.round_to_uncertainty(t_mean, t_unc, 1)
        u = self.Val.round_to_sig_dig(t_unc, 1)

        d={}
        d["TemperatureRoom"] = float(v)
        d["TemperatureRoomUnit"] = "K"
        d["TemperatureRoomUncertainty"] = float(u)
        d["TemperatureRoomCoverageFactor"] = k
        d["TemperatureRoomProb"] = self.k_trans[k]
        ana.store_dict(quant='AuxValues', d=d, dest=None)

        sec["RoomTemperature"] = self.to_si_pm_expr(v, u, unit)

        return sec

    def gen_temperature_head_entry(self, ana, sec, unit="K", k=2):
        t = ana.doc.get("AuxValues", {}).get("TemperatureHead")
        if t:
            unit = ana.doc.get("AuxValues", {}).get("TemperatureHeadUnit")
            t_unc = 0.5
            v = self.Val.round_to_uncertainty(t, t_unc, 2)
            u = self.Val.round_to_sig_dig(t_unc, 2)
            sec["HeadTemperature"] = self.to_si_expr(v, unit)

        return sec

    def gen_temperature_norm_entry(self, ana, sec, unit="K", k=2):
        t = ana.doc.get("AuxValues", {}).get("TemperatureNorm")
        if t:
            unit = ana.doc.get("AuxValues", {}).get("TemperatureNormUnit")
            t_unc = 0.1
            v = self.Val.round_to_uncertainty(t, t_unc, 2)
            u = self.Val.round_to_sig_dig(t_unc, 2)
            sec["NormTemperature"] = self.to_si_expr(v, unit)

        return sec

    def gen_temperature_estimated_entry(self, ana, sec, unit="K", k=2):
        t = ana.pick("Temperature", "frs5", "C")
        av_idx = ana.doc["AuxValues"]["AverageIndexFlat"]
        t = np.take(t, av_idx)
        t_mean = np.mean(t) - 4. + 273.15
        t_unc = 0.5

        v = self.Val.round_to_uncertainty(t_mean, t_unc, 2)
        u = self.Val.round_to_sig_dig(t_unc, 2)

        d={}
        d["TemperatureGas"] = float(v)
        d["TemperatureGasUnit"] = "K"
        d["TemperatureGasUncertainty"] = float(u)
        d["TemperatureGasCoverageFactor"] = k
        d["TemperatureGasProb"] = self.k_trans[k]
        d["TemperatureRoom"] = float(v)
        d["TemperatureRoomUnit"] = "K"
        d["TemperatureRoomUncertainty"] = float(u)
        d["TemperatureRoomCoverageFactor"] = k
        d["TemperatureRoomProb"] = self.k_trans[k]
        ana.store_dict(quant='AuxValues', d=d, dest=None)

        sec["EstimatedTemperature"] = self.to_si_pm_expr(v, u, unit)
        sec["GasTemperature"] = self.to_si_pm_expr(v, u, unit)
        sec["RoomTemperature"] = self.to_si_pm_expr(v, u, unit)

        return sec

    def gen_bakeout_entry(self, ana, sec, unit="K", k=2):
        t = ana.doc.get("AuxValues", {}).get("Bakeout")
        if t:
            T = ana.doc.get("AuxValues", {}).get("BakeoutTemperature")
            unit = ana.doc.get("AuxValues", {}).get("BakeoutTemperatureUnit")
            sec["BakeoutTemperature"] = self.to_si_expr(T, unit)

            t = ana.doc.get("AuxValues", {}).get("BakeoutTime")
            unit = ana.doc.get("AuxValues", {}).get("BakeoutTimeUnit")
            sec["BakeoutTime"] = self.to_si_expr(t, unit)

        return sec

    def gen_sputter_entry(self, ana, sec, unit="K", k=2):
        t = ana.doc.get("AuxValues", {}).get("Sputter")
        if t:
            p = ana.doc.get("AuxValues", {}).get("SputterPressure")
            unit = ana.doc.get("AuxValues", {}).get("SputterPressureUnit")
            sec["SputterPressure"] = self.to_si_expr(p, unit)

            t = ana.doc.get("AuxValues", {}).get("SputterTime")
            unit = ana.doc.get("AuxValues", {}).get("SputterTimeUnit")
            sec["SputterTime"] = self.to_si_expr(t, unit)

        return sec

    def gen_meas_date_entry(self, ana, sec):

        sec["MeasurementDate"] = self.Date.first_measurement()

        return sec

    def gen_min_max_entry(self, ana, sec, unit="Pa"):

        p_min, p_max, todo_unit = self.ToDo.get_min_max_pressure()
        conv = float(self.Const.get_conv(from_unit=todo_unit, to_unit=unit))
        sec["PressureRangeBegin"] = self.to_si_expr("{:.1e}".format(p_min*conv), unit)
        sec["PressureRangeEnd"] = self.to_si_expr("{:.1e}".format(p_max*conv), unit)

        return sec

    def gen_min_max_entry_direct_se2(self, ana, sec, unit="Pa"):

        ex = ana.org["Calibration"]["Measurement"]["Values"]["Expansion"]["Value"]
        av_idx = ana.doc["AuxValues"]["AverageIndexFlat"]
        p_cal = ana.pick("Pressure", "cal", unit)

        p_cal = [p_cal[i] for i in av_idx if ex[i]=="direkt"]

        if len(p_cal)>0:
            sec["PressureRangeDirectBegin"] =  self.to_si_expr("{:.1e}".format(min(p_cal)), unit)
            sec["PressureRangeDirectEnd"] =  self.to_si_expr("{:.1e}".format(max(p_cal)), unit)

        return sec


    def gen_temperature_correction(self, ana, sec):
        """ Sets the TemperatureCorrection flag to yes if
        * there is more than 1 point in the decade below 100 Pa and
        * `TemperatureHead` is not `None`
        """
        p_tdo, p_tdo_unit = self.ToDo.Pres.get_value_and_unit("target")
        conv = self.Const.get_conv(from_unit=p_tdo_unit, to_unit="Pa")

        p_tdo = conv * p_tdo
        #temperature correction only if more than 1 decade below 100 Pa

        p_tdo_evis = [p_tdo[i] for i in range(len(p_tdo)) if p_tdo[i] < 9.5]
        temperature_head = ana.doc.get("AuxValues", {}).get("TemperatureHead")
        if temperature_head and len(p_tdo_evis) > 1:
            sec["TemperatureCorrection"] = "yes"
        else:
            sec["TemperatureCorrection"] = "no"

        return sec

    def extr_val(self, x):
        if type(x) is list:
            return x[0]
        else:
            return x

    def gen_cdg_entry(self, ana, sec):

        e_vis = self.extr_val(ana.doc.get("AuxValues", {}).get("Evis"))
        u_vis = self.extr_val(ana.doc.get("AuxValues", {}).get("Uvis"))
        cf_vis = self.extr_val(ana.doc.get("AuxValues", {}).get("CFvis"))

        if e_vis is not None and u_vis is not None:
            sec["Evis"] = self.to_si_expr(self.Val.round_to_uncertainty(e_vis, u_vis, 2), "none")
            sec["UncertEvis"] = self.to_si_expr(self.Val.round_to_sig_dig(u_vis, 2), "none")


        if cf_vis and u_vis:
            sec["CFvis"] = self.to_si_expr(self.Val.round_to_uncertainty(cf_vis, u_vis, 2), "none")
            sec["UncertCFvis"] = self.to_si_expr(self.Val.round_to_sig_dig(u_vis, 2), "none")

        return sec

    def gen_uncert_offset_entry(self, ana, sec, unit="Pa"):

        val_fmt_str = "{:.1E}"
        ana_aux_values = ana.doc.get("AuxValues", {})
        av_idx = ana_aux_values.get("AverageIndex")
        uncert_contribs = ana_aux_values.get("OffsetUncertContrib")
        range_str = self.get_reduced_range_str(ana, av_idx)

        if uncert_contribs and "Unit" in uncert_contribs:
            if uncert_contribs["Unit"] is not unit:
                sys.exit("Unexpected as offset unit")
            entr = {}
            for r in uncert_contribs:
                value = None
                if r != "Unit":
                    if range_str:
                        if r in range_str:
                            value =  val_fmt_str.format(uncert_contribs[r])
                    else:
                        value =  val_fmt_str.format(uncert_contribs[r])

                    if value:
                        entr[r] = self.to_si_expr(value, unit)

            sec["OffsetUncertContrib"] = entr

        return sec

    def gen_srg_entry(self, ana, sec, k=2):
        """
            ..todo::

                s. issue https://a75436.berlin.ptb.de/vaclab/vpy/issues/15
        """

        sigma_null = ana.doc.get("AuxValues", {}).get("SigmaNull")
        sigma_corr_slope = ana.doc.get("AuxValues", {}).get("SigmaCorrSlope")
        sigma_std = ana.doc.get("AuxValues", {}).get("SigmaStd")

        if sigma_null and sigma_corr_slope and sigma_std:
            d = {}
            u_r = 2e-3
            v = self.Val.round_to_uncertainty(sigma_null, u_r, 2)
            sec["SigmaNull"] = self.to_si_expr(v, "none")
            d["SigmaNull"] = float(v)
            d["SigmaNullUnit"] = "1"
            d["SigmaNullUncertainty"] = float( self.Val.round_to_uncertainty(sigma_null * u_r, u_r, 2))
            d["SigmaNullCoverageFactor"] = k
            d["SigmaNullCoverageProb"] = self.k_trans[k]

            v = self.Val.round_to_uncertainty(sigma_corr_slope, sigma_std*k, 2)
            u = self.Val.round_to_sig_dig(sigma_std*k, 2)

            sec["SigmaCorrSlope"] = self.to_si_pm_expr(v, u, "1/Pa")
            d["SigmaCorrSlope"] = float(v)
            d["SigmaCorrSlopeUncertainty"] = float(u)
            d["SigmaCorrSlopeUnit"] = "1/Pa"
            d["SigmaCorrSlopeCoverageFactor"] = k
            d["SigmaCorrSlopeCoverageProb"] = self.k_trans[k]

            v_mean = "{:.4E}".format(ana.doc.get("AuxValues", {}).get("OffsetMean"))
            sec["OffsetMean"] = self.to_si_expr(v_mean, "DCR")

            v_sd = "{:.1E}".format(ana.doc.get("AuxValues", {}).get("OffsetStd"))
            sec["OffsetStd"] = self.to_si_expr(v_sd, "DCR")

            self.store_dict(quant='AuxValues', d=d, dest=None)

        return sec

    def make_measurement_data_section(self, ana, k=2, result_type="expansion", pressure_unit="Pa"):
        """The measurement data section should contain data
        belonging to one measurement (gas species, expansion or direct comp. etc) only.
        """
        sec = {}
        sec = self.gen_min_max_entry(ana, sec)
        sec = self.gen_uncert_offset_entry(ana, sec)

        if result_type == "cont_expansion":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_bakeout_entry(ana, sec)
            sec = self.gen_sputter_entry(ana, sec)

        if result_type == "srg_vg":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)

        if result_type == "expansion":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_temperature_correction(ana, sec)
            sec = self.gen_temperature_head_entry(ana, sec)
            sec = self.gen_temperature_norm_entry(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)

        if result_type == "se2_expansion":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_temperature_correction(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)

        if result_type == "se2_direct":
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)

        if result_type == "se2_expansion_direct":
            sec = self.gen_temperature_gas_entry_se2(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)
            sec = self.gen_temperature_correction(ana, sec)
            sec = self.gen_min_max_entry_direct_se2(ana, sec)
            sec = self.gen_cdg_entry(ana, sec)
            sec = self.gen_srg_entry(ana, sec)

        if result_type == "direct":
            sec = self.gen_temperature_gas_entry(ana, sec)
            sec = self.gen_temperature_room_entry(ana, sec)

        if result_type == "pressure_balance":
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_temperature_estimated_entry(ana, sec)

        if result_type == "rotary_piston_gauge":
            sec = self.gen_min_max_entry(ana, sec)
            sec = self.gen_min_max_entry(ana, sec)

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

    def make_off_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):
        off = self.get_reduced_pressure_off(ana, av_idx, pressure_unit)
        cal = self.get_reduced_pressure_cal(ana, av_idx, pressure_unit)
        u_off = self.get_reduced_uncert_off(ana, av_idx, error_unit)
        off_str = self.Val.round_to_uncertainty_array(off, u_off*cal, 2, scientific=True)

        return off_str

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

    def make_uncert_off_entry(self, ana, av_idx, pressure_unit, error_unit, k=2):

        cal = self.get_reduced_pressure_cal(ana, av_idx, pressure_unit)
        u_off = self.get_reduced_uncert_off(ana, av_idx, error_unit)

        u_off_k2_str = self.Val.round_to_sig_dig_array(u_off * cal, 2)

        return  u_off_k2_str

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

    def get_reduced_pressure_off(self, ana, av_idx, unit):
        off_dict = ana.pick_dict("Pressure", "offset")
        off_conv = self.Const.get_conv(from_unit=off_dict.get("Unit"), to_unit=unit)

        off = np.array(off_dict.get("Value"), dtype=np.float)  * off_conv
        off = ana.reduce_by_average_index(value=off, average_index=av_idx)

        return off

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

    def get_reduced_uncert_off(self, ana, av_idx, unit):
        u_off = ana.pick("Uncertainty", "offset", unit)
        u_off = ana.reduce_by_average_index(value=u_off, average_index=av_idx)

        return u_off

    def get_reduced_error(self, ana, av_idx, unit):
        error = ana.pick("Error", "ind_temperature_corr", unit)
        if error is None:
            error = ana.pick("Error", "ind", unit)
        error = ana.reduce_by_average_index(value=error, average_index=av_idx)

        return error

    def get_reduced_cf(self, ana, av_idx, unit):
        error = ana.pick("Error", "ind_temperature_corr", unit)
        if error is None:
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

        doc_aux_values = ana.doc.get("AuxValues", {})
        av_idx = doc_aux_values.get("AverageIndex")

        k = 2
        prob = 0.95

        cal_str = self.make_cal_entry(ana, av_idx, pressure_unit, error_unit)

        off_str = self.make_off_entry(ana, av_idx, pressure_unit, error_unit)
        ind_str = self.make_ind_entry(ana, av_idx, pressure_unit, error_unit)
        error_str = self.make_error_entry(ana, av_idx, pressure_unit, error_unit)
        cf_str = self.make_cf_entry(ana, av_idx, pressure_unit, error_unit)

        u_e_k2_str = self.make_uncert_error_entry(ana, av_idx, pressure_unit, error_unit)

        u_cf_k2_str = self.make_uncert_cf_entry(ana, av_idx, pressure_unit, error_unit)
        u_cal_k2_str = self.make_uncert_cal_entry(ana, av_idx, pressure_unit, error_unit)
        u_ind_k2_str = self.make_uncert_ind_entry(ana, av_idx, pressure_unit, error_unit)
        u_off_k2_str = self.make_uncert_off_entry(ana, av_idx, pressure_unit, error_unit)

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

        self.store_dict(quant="Table", d = {"Type": "offset",
                                            "DCCOut": True,
                                            "CoverageFactor": k,
                                            "CoverageProbability":prob,
                                            "Quantity": "Pressure",
                                            "Name": "indication at base pressure (offset)",
                                            "Uncertainty": u_off_k2_str,
                                            "DCCUnit": self.dcc_unit[pressure_unit],
                                            "Unit": pressure_unit,
                                            "Value": off_str,
                                            "HeadCell": self.head_cell["offset"],
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
