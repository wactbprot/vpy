import sys
import numpy as np
from ..document import Document
from ..constants import Constants
from ..values import Values, Pressure, AuxValues, Range

class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    def __init__(self, doc, dev):
        self.Const = Constants(doc)
        self.Vals = Values({})

        if "CalibrationObject" in dev:
            dev = dev.get('CalibrationObject')

        if "CustomerObject" in dev:
            dev = dev.get('CustomerObject')

        if "Uncertainty" in dev:
            self.uncert_dict = dev.get('Uncertainty')
        
        self.name = dev.get("Name")
        super().__init__(dev)

    def check_skip(self, uncert_dict, prop, skip):
        if prop in uncert_dict:
            if type(skip) is list:
                if uncert_dict[prop] in skip:
                    return True
                else:
                    return False
            if type(skip) is str:
                if  uncert_dict[prop] == skip:
                    return True
                else:
                    return False
            sys.exit("skip must be a list or string")
        else:
            return False

    def check_source_skip(self, uncert_dict, skip ): 
        if skip is not None:
            return self.check_skip(uncert_dict, "Source", skip)
        else:
            return False
    
    def check_type_skip(self, uncert_dict, skip ):
        if skip is not None:
            return self.check_skip(uncert_dict, "UncertType", skip)
        else:
            return False

    def check_take_list(self, uncert_dict, type_list):
        if type_list:
            for t in type_list:
                if uncert_dict["Type"].startswith(t):
                    return True
            return False
        else:
            return True ## all in case type_list is None

    def get_total_uncert(self, meas_vec, meas_unit, return_unit, res=None, skip_source=None, skip_type=None, take_type_list=None):
        """ Collects all Uncertainty contrib. for the given
        measurant (m). Calculates the quadratic sum and returns
        a np.array of the length as of m. Contributions with a certain source 
        (e.g. standard) or a certain type (e.g. B) can be skipped.

        .. note::

            * Typ-A: Ermittlung aus der statistischen Analyse mehrerer statistisch unabhängiger Messwerte aus einer Messwiederholung.
            * Typ-B: Ermittlung ohne statistische Methoden, beispielsweise durch Entnahme der Werte aus einem Kalibrierschein...

        .. todo::
                rewrite expression branch

        :param meas_vec: array containing values of the measurand the uncertainties are related to 
        :type meas_vec: np.array

        :param  meas_unit: unit of the  measurand
        :type  meas_unit: str

        :param return_unit: unit of the return values
        :type return_unit: str

        :returns: quadratic sum of uncertainties
        :rtype: np.array
        """
        
        uncert_arr = []
        if "uncert_dict" in self.__dict__:
            u_dict = self.uncert_dict
            for u_i in u_dict:
                if self.check_source_skip(u_i, skip_source):
                    continue
                if self.check_type_skip(u_i, skip_type):
                    continue
                if not self.check_take_list(u_i, take_type_list):
                    continue

                u = np.full(np.shape(meas_vec)[0], np.nan)
                u_val = u_i.get('Value', np.nan)
                range_unit = u_i.get('RangeUnit')
                from_val = u_i.get('From')
                to_val = u_i.get('To')
                u_unit = u_i.get('Unit')
                u_type = u_i.get('Type')
                u_descr = u_i.get("Description")

                from_val, to_val = self.convert_range_to_meas_unit(meas_unit, range_unit, from_val, to_val)
                range_index = self.get_match_index(meas_vec, from_val, to_val)
                u[range_index] = float(u_val)

                u, return_unit = self.convert_to_return_unit( u, u_unit, meas_vec, meas_unit, return_unit)

                uncert_arr.append( u )
                self.log.debug("Found type {}, append {} to uncertainty array".format(u_type, u))

                if res is not None:
                    res.store("Uncertainty" , "{dev}_{u_type}".format(dev=self.name, u_type=u_type), u, return_unit, descr=u_descr)

            uncert_total = self.Vals.square_array_sum(uncert_arr)
            uncert_total = self.Vals.replace_zero_by_nan(uncert_total)

            return uncert_total
        else:
            sys.exit("No uncertainty dict available")

    def get_match_index(self, meas_vec, from_val, to_val):
        N = np.shape(meas_vec)[0]
        n = np.full(N, False)
        a = np.full(N, True)

        if self.Vals.cnt_nan(meas_vec) == 0: ## todo rrename cnt_nan to cnt_not_nan
            return n
        if from_val and to_val:
            i = ((meas_vec > from_val) & (meas_vec < to_val))
            if len(i) > 0:
                return i
            else:
                return n
        else:
            return a
    def convert_range_to_meas_unit(self, meas_unit, range_unit, from_val, to_val):
        if from_val and to_val and meas_unit and range_unit:
            range_conv = self.Const.get_conv(from_unit=range_unit, to_unit=meas_unit)
            if meas_unit == "K":
                f = float(from_val) + range_conv
                t = float(to_val) + range_conv
            else:
                f = float(from_val) * range_conv
                t = float(to_val) * range_conv
            return f, t
        else:
            return None, None

    def convert_to_return_unit(self, u, u_unit, meas_vec, meas_unit, return_unit):
        if u_unit and meas_unit and return_unit:
            if u_unit != "1":
                conv = self.Const.get_conv(from_unit=u_unit, to_unit=return_unit)
                if u_unit == "C" and return_unit == "K":
                    u = u + conv
                else:
                    u = u * conv
            else:
                conv = self.Const.get_conv(from_unit=meas_unit, to_unit=return_unit)
                if meas_unit == "C" and return_unit == "K":
                    u = (u + conv) * meas_vec
                else:
                    u = u * meas_vec * conv
            return u, return_unit
        else:
            sys.exit("No uncertainty unit")

    def pressure(self, pressure_dict, temperature_dict, unit= 'Pa', gas= "N2"):
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float)

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

    def offset_uncert(self, ana, use_idx = None):
        """
        The offset uncertainty is calculated by means of `np.diff()`.
        Drift influences are avoided.
        """

        range_str = Range(ana.org).get_str("offset")
        ind = ana.pick("Pressure", "ind_corr", self.unit)
        offset = ana.pick("Pressure", "offset", self.unit)

        ## make elements not in use_idx nan:
        o = np.where([i not in use_idx for i in range(0,len(ind))])[0]
        for i in o:
            ind[i] = np.nan 
            offset[i] = np.nan 

        u = np.full(len(ind), np.nan) 
        uncert_contrib = {"Unit":self.unit}

        if range_str is not None:
            range_unique = np.unique(range_str)
            for r in range_unique:
                i_r = np.where(range_str == r)
                ## sometimes all offset[i_r] are nan
                all_nan = np.all(np.isnan(offset[i_r]))
                if np.shape(i_r)[1] > 0 and not all_nan:

                    m = np.nanmean(np.abs(np.diff(offset[i_r])))
                    u[i_r] = m/ind[i_r]
                    uncert_contrib[r] = m
        else:
            if len(offset) < 2:
                u = np.full(len(offset), 1.0e-5)
            else:
                m = np.nanmean(np.abs(np.diff(offset)))

                uncert_contrib["all"] = m
                u = m/ind


        ana.store_dict(quant='AuxValues', d={'OffsetUncertContrib':uncert_contrib}, dest=None)
        ana.store("Uncertainty", "offset", u, "1")

    def repeat_uncert(self, ana):

        p_list = ana.pick("Pressure", "ind_corr", "Pa")
        # *) bis 14.8.19
        #u = np.asarray([np.piecewise(p, [p <= 10, (p > 10 and p <= 950), p > 950], 
        #                                [0.0008,                 0.0003, 0.0001]).tolist() for p in p_list])
        cob = ana.org.get("Calibration", {}).get("CustomerObject", {})
        producer = cob.get("Device", {}).get("Producer", "missing").lower().replace("\s", "")
        type_head = cob.get("Setup", {}).get("TypeHead", "missing")
        standard = ana.org.get("Calibration", {}).get("ToDo", {}).get("Standard", "missing")

        if producer == "missing":
            msg = "No Producer in Device"
            self.log.warn(msg)
            sys.exit(msg)

        if standard == "missing":
            msg = "No Standard in ToDo"
            self.log.warn(msg)
            sys.exit(msg)

        if producer == "inficon" and standard == "FRS5":
            if type_head == "10Torr" or type_head == "100Torr":
                u = np.full(len(p_list), 2.9e-5)
            else:
                u = np.full(len(p_list), 1.0e-4)

        else: #MKS und andere
            u = np.asarray([np.piecewise(p, [p <= 9.5, (p > 9.5 and p <= 35.), (p > 35. and p <= 95.), p > 95.], 
                                            [0.0008,   0.0003,                0.0002,                   0.0001]).tolist() for p in p_list])            

        ana.store("Uncertainty", "repeat", u, "1")

    def device_uncert(self, ana):
        offset_uncert = ana.pick("Uncertainty", "offset", "1")
        repeat_uncert = ana.pick("Uncertainty", "repeat", "1")

        u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2))

        ana.store("Uncertainty", "device", u, "1")

