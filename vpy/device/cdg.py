import numpy as np
from scipy.interpolate import interp1d
from ..device.device import Device


class Cdg(Device):
    unit = "mbar"
    usable_decades = 3
    max_typehead_mbar = {
        "001Torr":  0.0013,
        "01Torr":   0.0133,
        "1Torr":    1.3332,
        "10Torr":   13.332,
        "100Torr":  133.32,
        "1000Torr": 1333.2
    }

    def __init__(self, doc, dev):

        super().__init__(doc, dev)

        self.doc = dev

        if "CalibrationObject" in dev:
            dev = dev['CalibrationObject']

        if "Name" in dev:
            self.name = dev["Name"]

        if "Setup" in dev:
            dev_setup = dev['Setup']
            if "TypeHead" in dev_setup:
                th = dev_setup['TypeHead']
                if th is not None:
                    self.max_p_mbar = self.max_typehead_mbar[th]
                    self.min_p_mbar = self.max_p_mbar / 10.0**self.usable_decades

        if "Interpol" in dev:
            self.interpol_x = self.get_value("p_ind", self.unit)
            self.interpol_y = self.get_value("e", "1")
            self.interpol_min = np.min(self.interpol_x)
            self.interpol_max = np.max(self.interpol_x)


    def pressure(self, pressure_dict, temperature_dict, unit= "Pa", gas= "N2"):
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = pressure_dict.get('Value')
        
        if pressure_unit == "V":
            #deal with it
            pass
        else:
            pressure = pressure_value *  self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)
        
        return pressure


    def store_interpol(self, p, e, u, p_unit, e_unit, u_unit):
        """Stores a dict containing ``p .. pressure``, ``e .. error`` and
        ``u .. uncertainty``

        """

        interpol = [{
            "Type": "p_ind",
            "Unit": p_unit,
            "Value": list(p)
        },
            {
            "Type": "e",
            "Unit": e_unit,
            "Value": list(e)
        },
            {
            "Type": "u",
            "Unit": u_unit,
            "Value": list(u)
        }]

        if "CalibrationObject" in self.doc:
            self.doc["CalibrationObject"]['Interpol'] = interpol

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

        f = self.interp_function(self.interpol_x, self.interpol_y)
        
        idx = (p_target*conv_target > self.interpol_min) & (p_target*conv_target < self.interpol_max)
        odx = (p_interpol*conv_target > self.interpol_min) & (p_interpol*conv_target < self.interpol_max)
        ndx = idx & odx
       
        if len(ndx) > 0:
            e[ndx] = f(p_interpol[ndx]*conv_interpol)

        return e

    def interp_function(self, x, y):
        return interp1d(x, y, kind="linear")

    def cal_interpol(self, p_cal, p_ind, uncert):
        """Calculates a interpolation vector for the relative
        error of indication and the uncertainty

        """

        p_cal_cut, p_ind_cut = self.cut_values(p_cal, p_ind)
        p_cal_cut, uncert_cut = self.cut_values(p_cal, uncert)


        f_error = self.interp_function(p_ind_cut, p_ind_cut / p_cal_cut - 1.0)
        f_uncert = self.interp_function(p_ind_cut, uncert_cut)
        p_ind_cut_nice = self.get_nice_vals(p_ind_cut)
        error_nice = f_error(p_ind_cut_nice)
        uncert_nice = f_uncert(p_ind_cut_nice)

        return p_ind_cut_nice, error_nice, uncert_nice

    def cut_values(self, p, s):
        i = np.argmin(abs(p -self.max_p_mbar))
        j = np.argmin(abs(p -self.min_p_mbar))
        return p[j:i+1], s[j:i+1]

    def get_nice_vals(self, x):
        ls = np.logspace(-5, 3, num=80)
        x_max = np.max(x)
        x_min = np.min(x)

        i = np.where(ls > x_min)[0][0]
        j = np.where(ls < x_max)[0][-1]

        return np.concatenate((np.array([x_min]), ls[i:j],  np.array([x_max])))


class InfCdg(Cdg):
    """Inficon CDGs are usable two decades only
    """

    usable_decades = 2

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
