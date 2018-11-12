import sys
import numpy as np
from scipy.interpolate import interp1d
from ..device.device import Device


class Cdg(Device):
    unit = "Pa"
    usable_decades = 3
    max_type_head = {
        "0.001Torr":  0.13,
        "0.01Torr":   1.33,
        "0.1Torr":   13.33,        
        "1Torr":    133.32,
        "10Torr":   1333.2,
        "100Torr":  13332.0,
        "1000Torr": 133320.0
    }
        
    interpol_pressure_points = np.logspace(-3, 5, num=101) # Pa 
    def __init__(self, doc, dev):
        super().__init__(doc, dev)
        self.doc = dev
        if 'CalibrationObject' in dev:
            dev = dev.get('CalibrationObject')
        if dev:
            self.name = dev.get('Name')
            dev_setup = dev.get('Setup')
            if dev_setup:
                type_head = dev_setup.get('TypeHead')
                if type_head:
                    if type_head in self.max_type_head:
                        self.max_p = self.max_type_head.get(type_head)
                        self.min_p = self.max_p / 10.0**self.usable_decades
                    else:
                        msg = "missing definition for type head {head}".format(head=type_head)
                        self.log.error(msg)
                        sys.exit(msg)
            if 'Interpol' in dev:
                self.interpol_x = self.get_value(value_type='p_ind', value_unit=self.unit)
                self.interpol_y = self.get_value(value_type='e', value_unit='1')
                self.interpol_min = np.min(self.interpol_x)
                self.interpol_max = np.max(self.interpol_x)
        else:
            msg = "Can't find device"
            self.log.error(msg)
            sys.exit(msg)

    def pressure(self, pressure_dict, temperature_dict, unit= 'Pa', gas= "N2"):
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = pressure_dict.get('Value')
        
        if pressure_unit == "V":
            #deal with it
            sys.exit('missing implementation')
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

    def error(self, p_cal, p_ind, p_unit):
        return np.divide(p_ind, p_cal) - 1.0, '1'

    def cal_interpol(self, pressure, error, uncertainty):
        """Calculates a interpolation vector for the relative
        error of indication and the uncertainty.

        This is done as follows:
            # conv_smooth
            # get_default_values
            # gen. interp. functions
            # interpolate default values

        """
        # smooth
        p = self.conv_smooth(pressure)
        e = self.conv_smooth(error)       
        u = self.conv_smooth(uncertainty)
        #interpolate function
        f_e = self.interp_function(p, e)
        f_u = self.interp_function(p, u)
        # default values
        p_default = self.get_default_values( np.nanmin(p), np.nanmax(p))
        # cal. interpol on default values
        e_default = f_e( p_default )
        u_default = f_u( p_default )

        return  p_default, e_default, u_default

    def conv_smooth(self, data, n=3):
        weights = np.ones(n) / n
        start_array = np.array([np.nanmean(data[0:n])])
        med_array = np.convolve(data, weights, mode='valid')
     
        end_array = np.array([np.nanmean(data[-n-1:-1])])

        return np.concatenate((start_array, med_array, end_array ))

    def rm_nan(self, x, ldx=None):
        if not isinstance(ldx, np.ndarray):
            ldx = np.logical_not(np.isnan(x))
        return x[ldx], ldx

    def shape_pressure(self, p):
        """Shapes the pressures by means of self.min and self.max
        in the unit self.unit

        :param p: pressure in the unit self.unit
        :type p: np.array
        """
        arr = np.full(p.shape[0], np.nan)
        i = np.where((p > self.min_p) & (p < self.max_p))
        arr[i] = p[i]
        return arr
       

    def get_default_values(self, x_min, x_max):
        i_min = np.where(self.interpol_pressure_points > x_min)[0][0]
        i_max = np.where(self.interpol_pressure_points < x_max)[0][-1]
        
        start_array = np.array([x_min])
        med_array = self.interpol_pressure_points[i_min:i_max]
        end_array = np.array([x_max])
        
        return np.concatenate((start_array, med_array, end_array )) 


class InfCdg(Cdg):
    """Inficon CDGs are usable two decades only
    """

    usable_decades = 2

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
