import sys
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from ..device.device import Device
from ..values import Values


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
        "10mbar": 1000.0, 
        "100mbar": 10000.0,
        "1000mbar": 100000.0
    }
    max_voltage = 10.0 # v
    type_head_cmr = { # Pa
        "1.1mbar": 110.0,
        "11mbar": 1100.0, 
        "110mbar": 11000.0,
        "1100mbar": 110000.0
    }
    cmr_base_factor =  { # Pa
        "1.1mbar": 100.0,
        "11mbar": 1000.0, 
        "110mbar":  10000.0,
        "1100mbar": 100000.0
    }
    cmr_offset = -1.0 # v
    cmr_factor = 0.125 # 1/v

    range_offset_trans = {
        "X1":"offset_x1",
        "X0.1":"offset_x0.1",
        "X0.01":"offset_x0.01",
    }
    
    range_extend = 0.005 # relativ
    interpol_pressure_points = np.logspace(-3, 5, num=81) # Pa 

    def e_vis_model(self, p, a, b, c, d):
        return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)
    
    def e_vis_bounds(self):
        return ([0, 0, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf])

    def get_e_vis_fit_params(self, p, e):
        params, _ = curve_fit(self.e_vis_model, p, e, bounds=self.e_vis_bounds(), maxfev=1000)
        return params

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
        self.doc = dev
        self.val = Values({})

        if 'CalibrationObject' in dev:
            dev = dev.get('CalibrationObject')
        
        if dev:
            self.name = dev.get('Name')
            dev_setup = dev.get('Setup')
            if dev_setup:
                use_from = dev_setup.get('UseFrom')
                use_to = dev_setup.get('UseTo')
                use_unit = dev_setup.get('UseUnit')
                type_head = dev_setup.get('TypeHead')
                conversion_type =  dev_setup.get('ConversionType')

                if use_from and use_to and use_unit:
                    conv = self.Const.get_conv(from_unit=use_unit, to_unit=self.unit)
                    self.max_p = float(use_to) * conv
                    self.min_p = float(use_from) * conv
                
                if type_head:

                    if type_head in self.type_head_factor:
                        self.max_p = self.type_head_factor.get(type_head)
                        self.min_p = self.max_p / 10.0**self.usable_decades
                
                        if not conversion_type:
                            self.conversion_type = "factor"

                    if type_head in self.type_head_cmr:
                        self.max_p = self.type_head_cmr.get(type_head)
                        self.min_p = self.max_p / 10.0**self.usable_decades
                
                        if not conversion_type:
                            self.conversion_type = "cmr"
                    
                if not self.max_p:
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

    def pressure(self, pressure_dict, temperature_dict, unit= 'Pa', gas= "N2"):
        """Converts the measured pressure in self.unit. If the unit is V
        this conversions are implemented: 
        
            * factor ... u * max_p / max_voltage
            * cmr ... (u + cmr_offset) * cmr_factor * cmr_base_factor[type_head]
        """
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'))
        
        if pressure_unit == "V":
            if self.conversion_type == "factor":
                return pressure_value * self.max_p/self.max_voltage

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

    def interp_function(self, x, y):
        return interp1d(x, y, kind="linear")

    def error(self, p_cal, p_ind, p_unit):
        return np.divide(p_ind, p_cal) - 1.0, '1'

    def cal_interpol(self, pressure, error):
        """Calculates a interpolation vector for the relative
        error of indication.

        This is done as follows:
            # conv_smooth ( --> no longer!, absorbs e-characteristics!) replaced by:
            # mean of mult meas. points
            # extrapolate values to the borders
            # get_default_values
            # gen. interp. functions
            # interpolate default values

        """
        # smooth
        ## p = self.conv_smooth(pressure)
        ## e = self.conv_smooth(error)       
        p = pressure
        e = error

        ## mean of mult meas. points
        idx = self.val.gatherby_idx(p, self.val.diff_less(0.2))
        p = [np.mean(p[i]) for i in idx]
        e = [np.mean(e[i]) for i in idx]
        
        # extrapolate
        p, e = self.fill_to_dev_borders(p, e)

        #interpolate function
        f_e = self.interp_function(p, e)
        
        # default values
        p_default = self.get_default_values( np.nanmin(p), np.nanmax(p))
        
        # cal. interpol on default values
        e_default = f_e( p_default )

        return  p_default, e_default
    
    def get_dmin_idx(self, d):
        m = np.amin(d)
        return np.where(d == m)[0][0]

    def fill_to_dev_borders(self, p, e):
        """Use the first/last value in the array of e and u
        as an extrapolation to the devive borders. Reduce the start/end
        value of p by `self.range_extend` to overcome possible intervall issues.
        """
        extr_p_low = np.array([self.min_p*(1.0 - self.range_extend)])
        d = p - extr_p_low
        i = self.get_dmin_idx(d)
        
        extr_e_low = np.array([e[i]])

        extr_p_high = np.array([self.max_p*(1.0 + self.range_extend)])
        d = extr_p_high - p
        j = self.get_dmin_idx(d)
        extr_e_high = np.array([e[j]])

        ret_p = np.concatenate( (extr_p_low, p, extr_p_high), axis=None)
        ret_e = np.concatenate( (extr_e_low, e, extr_e_high), axis=None)
        
        return ret_p, ret_e

    def conv_smooth(self, data, n=3):
        """Generates smooth data by a convolution.
        Bondaries (left and right) are calculated 
        from mean values.
        """
        
        weights = np.ones(n) / n

        start_array = np.array([np.nanmean(data[0:n])])
        med_array = np.convolve(data, weights, mode='valid')
        end_array = np.array([np.nanmean(data[-n-1:-1])])

        return np.concatenate((start_array, med_array, end_array ))

    def rm_nan(self, x, ldx=None):
        """Removes data from the given list by:
        
        * testing ``np.isnan()``
        * or the given (logical) vector ldx
        """
        if not isinstance(x,np.ndarray):
            sys.exit("rm_nan x argument has wrong type")
            
        if not isinstance(ldx, np.ndarray):
            ldx = np.logical_not(np.isnan(x))
           
        return x[ldx], ldx

    def shape_pressure(self, p):
        """Shapes the pressures by means of 
        ``self.min`` and ``self.max`` in the 
        unit ``self.unit``

        :param p: pressure in the unit self.unit
        :type p: np.array
        """
        p = np.nan_to_num(p)
        arr = np.full(p.shape[0], np.nan)
        l_list = np.less_equal(p, self.max_p)
        u_list = np.greater_equal(p, self.min_p)

        self.log.debug("lower list is: {l_list}".format(l_list=l_list))
        self.log.debug("upper list is: {u_list}".format(u_list=u_list))

        idx = np.where( u_list & l_list)
        self.log.debug("index vector is: {idx}".format(idx=idx))
        arr[idx] = p[idx]
        self.log.debug("returning array is: {arr}".format(arr=arr))
        
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
