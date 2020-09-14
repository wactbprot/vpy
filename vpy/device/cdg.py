import sys
import datetime
import numpy as np
from scipy.optimize import curve_fit
from ..device.device import Device
from ..values import Values, Range, Time
from ..constants import Constants

class Cdg(Device):
    unit = "Pa"
    usable_decades = 3
    type_head_factor = { # Pa
        "0.001Torr":  0.133322,
        "001Torr":   1.33322,
        "0.01Torr":   1.33322,
        "0.1Torr":   13.3322,
        "01Torr":   13.3322,
        "025Torr":   2.5*13.3322,
        "1Torr":    133.322,
        "5Torr":    5*133.322,
        "10Torr":   1333.22,
        "50Torr":    50*133.322,
        "100Torr":  13332.2,
        "500Torr":    500*133.322,
        "200Torr":  2*13332.2,
        "1000Torr": 133322.0,
        "01mbar": 10.0,
        "1mbar": 100.0,
        "1.1mbar": 100.0,
        "10mbar": 1000.0,
        "11mbar": 1000.0,
        "100mbar": 10000.0,
        "110mbar": 10000.0,
        "1000mbar": 100000.0,
        "1100mbar": 100000.0,
    }
    max_voltage = 10.0 # v
    type_head_cmr = { # Pa
        "0.11mbar": 11.0,
        "1.1mbar": 110.0,
        "11mbar": 1100.0,
        "110mbar": 11000.0,
        "1100mbar": 110000.0,
        "1mbar": 100.0,
        "10mbar": 1000.0,
        "100mbar": 10000.0,
        "1000mbar": 100000.0
    }
    cmr_base_factor =  { # Pa
        "0.11mbar": 10.0,
        "1.1mbar": 100.0,
        "11mbar": 1000.0,
        "110mbar":  10000.0,
        "1100mbar": 100000.0,
        "1mbar": 100.0,
        "10mbar": 1000.0,
        "100mbar":  10000.0,
        "1000mbar": 100000.0
    }
    cmr_offset = -1.0 # v
    cmr_factor = 0.125 # 1/v

    range_offset_trans = {
        "X1":"offset_x1",
        "X0.1":"offset_x0.1",
        "X0.01":"offset_x0.01",
    }
    range_mult = {
        "X1":1.,
        "X0.1":0.1,
        "X0.01":0.01,
    }

    def e_vis_limit(self):
        if self.max_p <= 14:
            return .1, 100.0, "Pa"
        else:
            return 1.0, 100.0, "Pa"

    def e_vis_model(self, p, a, b, c, d, e):
        return d + e / (a * p**2 + b * p + c * np.sqrt(p) + 1)

    def e_vis_bounds(self):
        return ([0, 0, 0, -np.inf, 0], [np.inf, np.inf, np.inf, np.inf, np.inf])

    def get_e_vis_fit_params(self, p, e):
        out = np.isnan(e)
        p = p[np.logical_not(out)]
        e = e[np.logical_not(out)]

        p_vis_lower_lim, p_vis_upper_lim, p_vis_lim_unit = self.e_vis_limit()

        idx = np.where(np.less_equal(p, p_vis_upper_lim) & np.greater_equal(p, p_vis_lower_lim))

        p = np.take(p, idx)[0]
        e = np.take(e, idx)[0]

        params, _ = curve_fit(self.e_vis_model, p, e, bounds=self.e_vis_bounds(), maxfev=10000)
        return params

    def __init__(self, doc, dev):
        self.Const = Constants(doc)

        if 'CalibrationObject' in dev:
            dev = dev.get('CalibrationObject')

        if dev:
            self.doc = dev
            dev_setup = dev.get('Setup')
            dev_device = dev.get('Device')
            if dev_setup:
                use_from = dev_setup.get('UseFrom')
                use_to = dev_setup.get('UseTo')
                use_unit = dev_setup.get('UseUnit')
                type_head = dev_setup.get('TypeHead')
                if type_head:
                    type_head = type_head.replace(".","")

                conversion_type =  dev_setup.get('ConversionType')

                if type_head:
                    self.producer = "missing"
                    if "mks" in dev_device["Producer"].lower():
                        self.producer = "mks"
                        if type_head in self.type_head_factor:
                            self.max_p = self.type_head_factor.get(type_head)
                            self.min_p = self.max_p / 10.0**self.usable_decades

                            if not conversion_type:
                                self.conversion_type = "factor"

                    if "edwards" in dev_device["Producer"].lower():
                        self.producer = "edwards"
                        if type_head in self.type_head_factor:
                            self.max_p = self.type_head_factor.get(type_head)
                            self.min_p = self.max_p / 10.0**self.usable_decades

                            if not conversion_type:
                                self.conversion_type = "factor"

                    if "inficon" in dev_device["Producer"].lower():
                        self.producer = "inficon"
                        if type_head in self.type_head_factor:
                            self.max_p = self.type_head_factor.get(type_head)
                            self.min_p = self.max_p / 10.0**self.usable_decades

                            if not conversion_type:
                                self.conversion_type = "factor"

                    if "leybold" in dev_device["Producer"].lower():
                        self.producer = "leybold"
                        if type_head in self.type_head_factor:
                            self.max_p = self.type_head_factor.get(type_head)
                            self.min_p = self.max_p / 10.0**self.usable_decades

                            if not conversion_type:
                                self.conversion_type = "factor"

                    if "pfeiffer" in dev_device["Producer"].lower():
                        self.producer = "pfeiffer"
                        if type_head in self.type_head_cmr:
                            self.max_p = self.type_head_cmr.get(type_head)
                            self.min_p = self.max_p / 10.0**self.usable_decades

                            if not conversion_type:
                                self.conversion_type = "cmr"

                if use_from and use_to and use_unit:
                    conv = self.Const.get_conv(from_unit=use_unit, to_unit=self.unit)
                    self.max_p = float(use_to) * conv
                    self.min_p = float(use_from) * conv


                if not "max_p" in dir(self):
                    msg = "missing definition for type head {head} and/or no use range given".format(head=type_head)
                    self.log.error(msg)
                    sys.exit(msg)

                if conversion_type:
                    self.conversion_type = conversion_type

                if type_head:
                    self.type_head = type_head

        if 'Interpol' in dev:
            # pressure
            v, u = self.get_value_and_unit('p_ind')
            conv = self.Const.get_conv(from_unit=u, to_unit=self.unit)
            self.interpol_p = v * conv
            # error
            self.interpol_e = self.get_value(value_type='e', value_unit='1')

            interpol_min = np.min(self.interpol_p)
            interpol_max = np.max(self.interpol_p)

            if self.min_p > interpol_min:
                self.interpol_min = self.min_p
            else:
                self.interpol_min = interpol_min
            if self.max_p > interpol_max:
                self.interpol_max =  interpol_max
            else:
                self.interpol_max =  self.max_p

        else:
            msg = "Can't find device"
            self.log.error(msg)
            sys.exit(msg)

        super().__init__(doc, dev)

    def temperature_correction(self, x_dict, p_cal_dict, t_gas_dict, t_head_dict, t_norm_dict, x_vis, x_vis_unit):

        if x_dict.get("Unit") !=  x_vis_unit:
            sys.exit("wrong x units")

        if t_gas_dict.get("Unit") !=  t_norm_dict.get("Unit") or t_gas_dict.get("Unit") !=  t_head_dict.get("Unit"):
            sys.exit("wrong t units")

        p_vis_lower_lim, p_vis_upper_lim, p_vis_lim_unit = self.e_vis_limit()
        if p_cal_dict.get("Unit") != p_vis_lim_unit:
            sys.exit("wrong p units")

        x = np.array(x_dict.get("Value"))
        x_vis = np.array(x_vis)
        t_gas = np.array(t_gas_dict.get("Value"))
        t_head = np.array(t_head_dict.get("Value"))
        t_norm = np.array(t_norm_dict.get("Value"))
        p_cal = np.array(p_cal_dict.get("Value"))

        ec = np.full(len(x), np.nan)

        idx = np.where(np.less_equal(p_cal, p_vis_upper_lim))
        odx = np.where(np.greater(p_cal, p_vis_upper_lim))

        if np.shape(idx)[1] == 0:
            return x
        else:
            ec[idx] = x_vis + (np.take(x, idx) - x_vis) * (np.sqrt(t_head/t_norm) - 1)/(np.sqrt(t_head/np.take(t_gas, idx)) - 1)

        if np.shape(odx)[1] != 0:
            ec[odx] = np.take(x, odx)

        return  ec

    def pressure(self, pressure_dict, temperature_dict, range_dict=None, unit= 'Pa', gas= "N2"):
        """Converts the measured pressure in self.unit. If the unit is V
        this conversions are implemented:

            * factor ... u * max_p / max_voltage
            * cmr ... (u + cmr_offset) * cmr_factor * cmr_base_factor[type_head]
        """
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float)

        if pressure_unit == "V":
            if self.conversion_type == "factor":
                if range_dict:
                    range_mult = np.array([self.range_mult.get(x) for x in range_dict.get('Value') ])
                    p = pressure_value * self.max_p/self.max_voltage * range_mult
                else:
                    p = pressure_value * self.max_p/self.max_voltage

                return p

            if self.conversion_type == "cmr":
                return (pressure_value + self.cmr_offset) * self.cmr_factor * self.cmr_base_factor[self.type_head]

            msg = "conversion type not implemented"
            self.log.error(msg)
            sys.exit(msg)
        else:
            return pressure_value * self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)

    def get_error_interpol(self, p_interpol, unit_interpol, p_target=None, unit_target=None):
        """
        Returns the interpolation error at the points where:

        (p_target > self.interpol_min) & (p_target < self.interpol_max)

        .. todo::

                implement expected unit of the return value
        """
        N = len(p_interpol)
        e = np.full(N, np.nan)

        if unit_target is None and p_target is None:
            unit_target = unit_interpol
            p_target = p_interpol

        if unit_interpol == self.unit:
            conv_interpol = 1.0
        else:
            conv_interpol = self.Const.get_conv(unit_interpol, self.unit)

        if unit_target == self.unit:
            conv_target = 1.0
        else:
            conv_target = self.Const.get_conv(unit_target, self.unit)

        f_e = self.interp_function(self.interpol_p, self.interpol_e)

        idx = (p_target*conv_target > self.interpol_min) & (p_target*conv_target < self.interpol_max)
        odx = (p_interpol*conv_target > self.interpol_min) & (p_interpol*conv_target < self.interpol_max)
        ndx = idx & odx

        if len(ndx) > 0:
            e[ndx] = f_e(p_interpol[ndx]*conv_interpol)


        return e
    def error(self, p_cal, p_ind, p_unit):
        return np.divide(p_ind, p_cal) - 1.0, '1'

    def offset_uncert(self, ana, use_idx = None):
        """
        The offset uncertainty is calculated by means of `np.diff(offset)`.
        Drift influences are avoided.
        """

        range_str = Range(ana.org).get_str("offset")
        ind = ana.pick("Pressure", "ind_corr", self.unit)
        offset = ana.pick("Pressure", "offset", self.unit)

        ## make elements not in use_idx nan:
        if  use_idx is not None:
            o = np.where([i not in use_idx for i in range(0, len(ind))])[0]
            for i in o:
                ind[i] = np.nan
                offset[i] = np.nan

        u = np.full(len(ind), np.nan)

        ## time expan.:
        t_ms = Time(ana.org).get_str("amt_fill")
        if t_ms is None:
            ## time direct & frs5:
            t_ms = Time(ana.org).get_str("amt_meas")

        days = [datetime.datetime.fromtimestamp(int(t)/1000.0).day for t in t_ms]

        u_rel_day_arr = {}
        u_abs_day = {}

        for day in np.unique(days):
            uncert_contrib = {}
            ddx = np.where(np.equal(days, day))
            day_offset = np.take(offset, ddx)[0]
            day_ind = np.take(ind, ddx)[0]

            if range_str is not None:
                day_range_str = np.take(range_str, ddx)[0]
                range_unique = np.unique(day_range_str)
                for r in range_unique:
                    i_r = np.where(day_range_str == r)
                    ## sometimes all day_offset[i_r] are nan
                    all_nan = np.all(np.isnan(day_offset[i_r]))
                    if len(i_r) > 0 and not all_nan:
                        m = np.nanmean(np.abs(np.diff(day_offset[i_r])))
                        if m == 0.0:
                            m = self.ask_for_offset_uncert(day_offset[i_r], self.unit, day_range_str=r)

                        uncert_contrib[r] = m
                        u_abs_day[day] = uncert_contrib
                        u[i_r] = m/day_ind[i_r]
            else:
                if len(day_offset) < 2:
                    m = self.ask_for_offset_uncert(day_offset, self.unit)
                else:
                    m = np.nanmean(np.abs(np.diff(day_offset)))

                    if m == 0.0:
                        ## Abschätzung 0.1% vom kleinsten p_ind
                        m = self.ask_for_offset_uncert(day_offset, self.unit)

                    uncert_contrib["all"] = m
                    u_abs_day[day] = uncert_contrib
                    u = m/day_ind
            u_rel_day_arr[day] = u

        u_rel_arr = np.array([])
        u_abs = {}

        for day in np.unique(days):
            u_rel_arr = np.concatenate((u_rel_arr, u_rel_day_arr[day]), axis=None)
            for e in u_abs_day[day]:
                if not e in u_abs:
                    u_abs[e] =  np.array([])
                u_abs[e] = np.append(u_abs[e], u_abs_day[day][e])


        for e in u_abs:
            u_abs[e] = np.mean(u_abs[e])


        u_abs["Unit"] = self.unit
        ana.store_dict(quant='AuxValues', d={'OffsetUncertContrib':u_abs}, dest=None)
        ana.store("Uncertainty", "offset", u_rel_arr, "1")

    def repeat_uncert(self, ana, cmc=True):
        ok = False
        p_list = ana.pick("Pressure", "ind_corr", "Pa")
        if self.producer == "missing":
            msg = "No Producer in Device"
            self.log.warn(msg)
            sys.exit(msg)

        if self.ToDo.get_standard() == "missing":
            msg = "No Standard in ToDo"
            self.log.warn(msg)
            sys.exit(msg)

        if self.producer == "inficon" and self.ToDo.get_standard() == "FRS5":
            if self.type_head == "10Torr" or self.type_head == "100Torr":
                u = np.full(len(p_list), 2.9e-5)
            else:
                u = np.full(len(p_list), 1.0e-4)
            ok = True

        if not cmc and self.type_head == "01Torr" and self.producer == "mks" and self.ToDo.get_standard() == "SE3":
            ## calculation follows:
            ## http://a73435.berlin.ptb.de:82/lab/tree/QS/QSE-SE3-20-6-device_repeatability.ipynb

            m = 9.3e-06 #Pa/Pa
            b = 0.00026 #Pa
            u_rel_min = 0.0015 # 1
            p_min = 0.167 # Pa

            u = np.full(len(p_list), u_rel_min)
            idx = np.where(p_list > p_min)[0]
            if len(idx) > 0:
                u[idx] = m + b/p_list[idx]

            ok = True

        if not cmc and self.type_head == "1Torr" and self.producer == "mks" and self.ToDo.get_standard() == "SE3":
            ## calculation follows:
            ## http://a73435.berlin.ptb.de:82/lab/tree/QS/QSE-SE3-20-6-device_repeatability.ipynb

            m = 2.53e-05 #Pa/Pa
            b = 0.00047 #Pa
            u_rel_min = 0.000731 # 1
            p_min = 0.67 # Pa

            u = np.full(len(p_list), u_rel_min)
            idx = np.where(p_list > p_min)[0]
            if len(idx) > 0:
                u[idx] = m + b/p_list[idx]

            ok = True


        if not ok: #Rest
            u = np.asarray([np.piecewise(p, [p <= 9.5, (p > 9.5 and p <= 35.), (p > 35. and p <= 95.), p > 95.],
                                            [0.0008,   0.0003,                0.0002,                   0.0001]).tolist() for p in p_list])

        ana.store("Uncertainty", "repeat", u, "1")

    def device_uncert(self, ana):
        offset_uncert = ana.pick("Uncertainty", "offset", "1")
        repeat_uncert = ana.pick("Uncertainty", "repeat", "1")


        digit_uncert_dict = ana.pick_dict("Uncertainty", "digit")
        if digit_uncert_dict is not None:
            if digit_uncert_dict.get("Unit") == "Pa":
                p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")
                digit_uncert = ana.pick("Uncertainty", "digit", "Pa")
                u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2) + np.power(digit_uncert/p_ind_corr, 2))
            else:
                digit_uncert = ana.pick("Uncertainty", "digit", "1")
                u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2) + np.power(digit_uncert, 2))
        else:
            u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2))


        add_uncert = ana.pick_dict("Uncertainty", "add")
        if add_uncert is not None:
            add_unit = add_uncert.get("Unit")
            if add_unit == "Pa":
                p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")
                add_uncert = ana.pick("Uncertainty", "add", "Pa")
                u = np.sqrt(np.power(u, 2) + np.power(add_uncert/p_ind_corr, 2))

            if add_unit == "1":
                add_uncert = ana.pick("Uncertainty", "add", "1")
                u = np.sqrt(np.power(u, 2) + np.power(add_uncert, 2))

        ana.store("Uncertainty", "device", u, "1")


class InfCdg(Cdg):
    """Inficon CDGs are usable two decades only
    """

    usable_decades = 2

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
