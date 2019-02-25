import sys
import numpy as np
from ..document import Document
from ..constants import Constants


class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    def __init__(self, doc, dev):
        self.Const = Constants(doc)

        if "CalibrationObject" in dev:
            dev = dev.get('CalibrationObject')

        if "CustomerObject" in dev:
            dev = dev.get('CustomerObject')

        if "Uncertainty" in dev:
            self.uncert_dict = dev.get('Uncertainty')

        super().__init__(dev)

    def get_total_uncert(self, meas, unit, runit):
        """ Collects all Uncertainty contrib. for the given
        measurant (m). Calculates the quadratic sum and returns
        a np.array of the length as of m.

        .. todo::
                rewrite expression branch

        :param meas: array containing values of the measurand the uncertainties are related to 
        :type meas: np.array

        :param unit: unit of the  measurand
        :type unit: str

        :param runit: unit of the return values
        :type runit: str

        :returns: quadratic sum of uncertainties
        :rtype: np.array
        """
        range_enlarge = 0.1
        u_arr = []
        N = np.shape(meas)[0]

        if "uncert_dict" in self.__dict__:
            u_dict = self.uncert_dict
            for u_i in u_dict:
                u = np.full(N, np.nan)
                idx = np.full(N, True)

                if "From" in u_i and "To" in u_i and "RangeUnit" in u_i:
                    range_conv = self.Const.get_conv(u_i.get('RangeUnit'), unit)
                    if unit == "K":
                        f = float(u_i.get('From')) + range_conv
                        t = float(u_i.get('To')) + range_conv
                    else:
                        f = float(u_i.get('From')) * range_conv
                        t = float(u_i.get('To')) * range_conv

                    i = (meas > f*(1-range_enlarge)) & (meas < t*(1+range_enlarge))
                    if len(i) > 0:
                        idx = i

                if "Value" in u_i:
                    u[idx] = float(u_i.get('Value'))

                if "Expression" in u_i:
                    # untested
                    #fn = sym.lambdify(self.symb, u_i["Expression"], "numpy")
                    # check units before use meas
                    #u = fn(meas)
                    pass

                if "Unit" in u_i:
                    if u_i.get('Unit') != "1":
                        conv = self.Const.get_conv(u_i.get('Unit'), runit)
                        if unit == "C" and runit == "K":
                            u = u + conv
                        else:
                            u = u * conv
                    else:
                        conv = self.Const.get_conv(unit, runit)
                        if unit == "C" and runit == "K":
                            u = (u + conv) * meas
                        else:
                            u = u * meas * conv

                self.log.debug("found type {}, append {} to uncertainty array".format(u_i.get('Type'), u))
                u_arr.append( u )

            u = np.sqrt(np.nansum(np.power(u_arr, 2), axis=0))

            i = (u == 0.0)
            if len(i) > 0:
                u[i] = np.nan

            return u
        else:
            sys.exit("No uncertainty dict available")

    
    def pressure(self, pressure_dict, temperature_dict, unit= 'Pa', gas= "N2"):
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'))
        
        if pressure_unit == "V":
           pressure = pressure_value * self.max_p/self.max_voltage
        else:
            pressure = pressure_value *  self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)
        
        return pressure
