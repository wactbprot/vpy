import sys
import numpy as np
from ..document import Document
from ..constants import Constants
from ..values import Pressure, AuxValues, Range

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

    def get_total_uncert(self, meas, unit, runit, res=None):
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
                if res is not None:
                    uncert_type = "{dev}_{t}".format(dev=self.name, t=u_i.get('Type'))
                    res.store("Uncertainty" , uncert_type, u, runit, descr=u_i.get("Description"))

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
    
    def range_trans(self, ana):
        """Traverses Range to analysis section.
        
        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        range_str = Range(ana.org).get_str("ind")
        if range_str is not None:
            ana.store('Range', 'ind', range_str, '1')

    def offset_uncert(self, ana):
        """Calculates the standard deviation of the *single* value of the 
        offset sample stored in ``Measurement.AuxValues.Pressure``
        """
       
        pres = Pressure(ana.org)
        aux = AuxValues(ana.org)

        ind, ind_unit = pres.get_value_and_unit("ind")
        range_str = Range(ana.org).get_str("ind")

        u = np.full(len(ind), np.nan)
        if range_str is not None:
            range_unique = np.unique(range_str)
            for r in range_unique:
                i_r = np.where(range_str == r)
                if np.shape(i_r)[1] > 0:
                    range_type = self.range_offset_trans[r]
                    offset_sample_value, sample_unit = aux.get_value_and_unit(d_type=range_type)
                    if ind_unit == sample_unit:
                        std = np.nanstd(offset_sample_value)
                        u[i_r] = np.abs(std/ind[i_r])
                    else:
                        sys.exit("ind measurement unit and sample unit dont match")
        else:
            ## simple offset sample stored in Measurement.AuxValues.Pressure
            offset_sample_value, sample_unit = aux.get_value_and_unit(d_type="offset")
            if ind_unit == sample_unit:
                std = np.nanstd(offset_sample_value)
                if std < 1e-12: ## all the same
                    self.log.warn("standard deviation of offset sample < E-12, est. with 5% of measured value")
                    u = np.abs(np.nanmean(offset_sample_value)*0.05/ind)
                else:
                    u = np.abs(std/ind)
        ana.store("Uncertainty", "offset", u, "1")

    def repeat_uncert(self, ana):
        
        p_list = ana.pick("Pressure", "ind_corr", "Pa")
        # *) bis 14.8.19
        #u = np.asarray([np.piecewise(p, [p <= 10, (p > 10 and p <= 950), p > 950], 
        #                                [0.0008,                 0.0003, 0.0001]).tolist() for p in p_list])

        u = np.asarray([np.piecewise(p, [p <= 9.5, (p > 9.5 and p <= 35.), (p > 35. and p <= 95.), p > 95.], 
                                        [0.0008,   0.0003,                0.0002,                   0.0001]).tolist() for p in p_list])

        ana.store("Uncertainty", "repeat", u, "1")

    def device_uncert(self, ana):
        offset_uncert = ana.pick("Uncertainty", "offset", "1")
        repeat_uncert = ana.pick("Uncertainty", "repeat", "1")
        
        u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2))
        
        ana.store("Uncertainty", "device", u, "1")
            