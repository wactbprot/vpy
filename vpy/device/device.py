import sys
import numpy as np
from ..document import Document
from ..values import Values, Pressure, AuxValues, Range
from ..constants import Constants
from ..todo import ToDo
from scipy.interpolate import interp1d

class Device(Document):
    """ Class should be complete with
    self.Const and self.Dev, nothing more
    """

    range_extend = 0.005 # relativ
    interpol_pressure_points = np.logspace(-3, 5, num=81) # Pa

    def __init__(self, doc, dev):

        self.ToDo = ToDo(doc)
        self.Vals = Values({})
        self.Const = Constants(doc)

        if "CalibrationObject" in dev:
            dev = dev.get('CalibrationObject')

        if "CustomerObject" in dev:
            dev = dev.get('CustomerObject')

        if "Uncertainty" in dev:
            self.uncert_dict = dev.get('Uncertainty')

        self.name = dev.get("Name")
        self.dev_class = dev.get("Class")

        super().__init__(dev)

    def interp_function(self, x, y):
        return interp1d(x, y, kind="linear")

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

    def cal_interpol(self, x, y):
        """Calculates a interpolation vector for y vs. x.

        This is done as follows:
            # conv_smooth ( --> no longer!, absorbs e-characteristics!) replaced by:
            # mean of mult meas. points
            # extrapolate values to the borders
            # get_default_values
            # gen. interp. functions
            # interpolate default values

        """
        ## mean of mult meas. points
        idx = self.Vals.gatherby_idx(x, self.Vals.diff_less(0.2))
        x = [np.mean(x[i]) for i in idx]
        y = [np.mean(y[i]) for i in idx]

        # extrapolate
        x, y = self.fill_to_dev_borders(x, y)

        #interpolate function
        f_y = self.interp_function(x, y)

        # default values
        x_default = self.get_default_values( np.nanmin(x), np.nanmax(x))

        # cal. interpol on default values
        y_default = f_y( x_default )

        return  x_default, y_default

    def fill_to_dev_borders(self, p, e):
        """Use the first/last value in the array of e and u
        as an extrapolation to the devive borders. Reduce the start/end
        value of p by `self.range_extend` to overcome possible intervall issues.
        """
        extr_p_low = np.array([self.min_p*(1.0 - self.range_extend)])
        d = p - extr_p_low
        i = np.argmin(d)

        extr_e_low = np.array([e[i]])

        extr_p_high = np.array([self.max_p*(1.0 + self.range_extend)])
        d = extr_p_high - p
        j = np.argmin(d)
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
        idx = np.where( u_list & l_list)

        arr[idx] = p[idx]

        return arr

    def get_default_values(self, x_min, x_max):
        i_min = np.where(self.interpol_pressure_points > x_min)[0][0]
        i_max = np.where(self.interpol_pressure_points < x_max)[0][-1]

        start_array = np.array([x_min])
        med_array = self.interpol_pressure_points[i_min:i_max]
        end_array = np.array([x_max])

        return np.concatenate((start_array, med_array, end_array ))

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

    def get_total_uncert(self, meas_vec, meas_unit, return_unit, res=None, skip_source=None, skip_type=None, take_type_list=None, prefix=True):
        """Collects all Uncertainty contrib. for the given measurement vector
        `meas_vec`. Calculates the quadratic sum and returns a
        `np.array` of the length as of `meas_vec`. Contributions with
        a certain source (e.g. standard) or a certain type (e.g. B)
        can be skipped.

        For digitalisation uncertainties an `Resolution` key may be
        provided.

        .. note::

            Typ-A: Ermittlung aus der statistischen Analyse mehrerer
            statistisch unabhängiger Messwerte aus einer
            Messwiederholung.
            Typ-B: Ermittlung ohne statistische
            Methoden, beispielsweise durch Entnahme der Werte aus
            einem Kalibrierschein...

        :param meas_vec: array containing values of the measurment
                         vector the uncertainties are related to
        :type meas_vec: np.array

        :param  meas_unit: unit of meas_vec
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

                u_val = u_i.get('Value')
                digit = u_i.get('Resolution')

                range_unit = u_i.get('RangeUnit')
                from_val = u_i.get('From')
                to_val = u_i.get('To')
                u_unit = u_i.get('Unit')
                u_type = u_i.get('Type')
                u_descr = u_i.get("Description")

                from_val, to_val = self.convert_range_to_meas_unit(meas_unit, range_unit, from_val, to_val)
                range_index = self.get_match_index(meas_vec, from_val, to_val)

                if u_val is not None:
                    u[range_index] = float(u_val)
                    u, return_unit = self.convert_to_return_unit( u, u_unit, meas_vec, meas_unit, return_unit)

                if digit is not None:
                    u[range_index] = self.cal_abs_digit_uncert(meas_vec[range_index], digit)
                    u, return_unit = self.convert_to_return_unit( u, meas_unit, meas_vec, meas_unit, return_unit)

                uncert_arr.append( u )
                if prefix:
                    type_name="{dev}_{u_type}".format(dev=self.name, u_type=u_type)
                else:
                    type_name="{u_type}".format(u_type=u_type)

                if res is not None:
                    res.store("Uncertainty", type_name, u, return_unit, descr=u_descr)

            uncert_total = self.Vals.square_array_sum(uncert_arr)
            uncert_total = self.Vals.replace_zero_by_nan(uncert_total)

            return uncert_total
        else:
            sys.exit("No uncertainty dict available")

    def cal_abs_digit_uncert(self, meas_vec, digit):
        exp = np.floor(np.log10(np.abs(meas_vec)))
        return [digit * 0.29 * 10**e for e in exp]

    def get_match_index(self, meas_vec, from_val, to_val):
        if type(from_val) == np.ndarray:
            from_val = from_val[0]
        if type(to_val) == np.ndarray:
            to_val = to_val[0]

        N = np.shape(meas_vec)[0]
        n = np.full(N, False)
        a = np.full(N, True)

        if self.Vals.cnt_nan(meas_vec) == 0: ## todo rrename cnt_nan to cnt_not_nan
            return n
        if from_val and to_val:
            i = [ x > from_val and x < to_val for x in  meas_vec]
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
            if return_unit == "1" and u_unit != "1" and u_unit == meas_unit:
                return u/meas_vec, return_unit

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

    def pressure(self, pressure_dict, temperature_dict, range_dict=None, unit= 'Pa', gas= "N2"):
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float)

        if pressure_unit == "V":
           pressure = pressure_value * self.max_p/self.max_voltage
        else:
            pressure = pressure_value *  self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)

        return pressure

    def range_trans(self, ana):
        """Traverses range vector to the analysis section.

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        range_str = Range(ana.org).get_str("ind")
        if range_str is not None:
            ana.store('Range', 'ind', range_str, '1')

    def ask_for_offset_uncert(self, offset, unit, range_str="all"):
        """ Asks for u(offset).
        """
        print("\n\n\nOffset in {}:\n".format(unit))
        print(offset)
        print("\nUncertainty contribution  of offset (range: {range_str})\n can not be derived from measurement:\n\n".format(range_str=range_str))
        u =  float(input("\n\nType in offset uncertainty in {}: ".format(unit)))
        d =  input("\n\nType in the distribution of the given uncerainty: r[ect] or n[ormal] (default): ")

        if d.startswith("r"):
            return u*0.29
        else:
            return u

    def device_uncert(self, ana):

        offset_uncert = ana.pick("Uncertainty", "offset", "1")
        repeat_uncert = ana.pick("Uncertainty", "repeat", "1")
        emis_uncert  = ana.pick("Uncertainty", "emis", "1")

        digit_uncert_dict = ana.pick_dict("Uncertainty", "digit")

        add_uncert = ana.pick_dict("Uncertainty", "add")

        add_rel_uncert = ana.pick_dict("Uncertainty", "add_rel")
        add_abs_uncert = ana.pick_dict("Uncertainty", "add_abs")

        if digit_uncert_dict is not None:
            if digit_uncert_dict.get("Unit") == "Pa":
                p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa" )
                digit_uncert = ana.pick("Uncertainty", "digit", "Pa")
                u = np.sqrt(np.power(offset_uncert, 2) +
                            np.power(repeat_uncert, 2) +
                            np.power(digit_uncert/p_ind_corr, 2))
            else:
                digit_uncert = ana.pick("Uncertainty", "digit", "1")
                u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2) + np.power(digit_uncert, 2))
        else:
            u = np.sqrt(np.power(offset_uncert, 2) + np.power(repeat_uncert, 2))

        if add_uncert is not None:
            add_unit = add_uncert.get("Unit")
            if add_unit == "Pa":
                p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")
                add_uncert = ana.pick("Uncertainty", "add", "Pa")

                u = np.sqrt(np.power(u, 2) + np.power(add_uncert/p_ind_corr, 2))

            if add_unit == "1":
                add_uncert = ana.pick("Uncertainty", "add", "1")
                u = np.sqrt(np.power(u, 2) + np.power(add_uncert, 2))

        if add_rel_uncert is not None:
            # rel uncert is already processed so that the unit should be Pa
            add_unit = add_rel_uncert.get("Unit")
            if add_unit == "Pa":
                p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")
                add_rel_uncert = ana.pick("Uncertainty", "add_rel", "Pa")

                u = np.sqrt(np.power(u, 2) + np.power(add_rel_uncert/p_ind_corr, 2))

        if add_abs_uncert is not None:
            add_unit = add_abs_uncert.get("Unit")
            if add_unit == "Pa":
                p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")
                add_abs_uncert = ana.pick("Uncertainty", "add_abs", "Pa")

                u = np.sqrt(np.power(u, 2) + np.power(add_abs_uncert/p_ind_corr, 2))

        if emis_uncert is not None:
            u = np.sqrt(np.power(u, 2) + np.power(emis_uncert, 2))

        ana.store("Uncertainty", "device", u, "1")


    def offset_uncert(self, ana,  reject_index = None):
        """
        The offset uncertainty is calculated by means of `np.diff(offset)`.
        Drift influences are avoided.
        """

        ind = ana.pick("Pressure", "ind_corr", ana.pressure_unit)
        offset = ana.pick("Pressure", "offset", ana.pressure_unit)

        if reject_index:
            for i in reject_index:
                ind[i] = np.nan
                offset[i] = np.nan

        ##
        u_rel_arr = np.full(len(ind), np.nan)
        u_abs_arr = np.full(len(ind), np.nan)
        offset_contrib = {"Unit": ana.pressure_unit}

        m = np.nanmean(np.abs(np.diff(offset)))
        if m == 0.0:
            m = self.ask_for_offset_uncert(offset, ana.pressure_unit, range_str="all")

        offset_contrib["all"] = m
        u_abs_arr = m

        ana.store_dict(quant='AuxValues', d={'OffsetUncertContrib': offset_contrib}, dest=None)
        ana.store("Uncertainty", "offset",  m/ind, "1")

    def repeat_uncert(self, ana):

        p_ind = ana.pick("Pressure", "ind_corr", ana.pressure_unit)
        u_rel = np.full(len(p_ind), self.rel_repeat_uncert)

        ana.store("Uncertainty", "repeat", u_rel, "1")

    def digit_uncert(self, ana):

        p_ind = ana.pick("Pressure", "ind", ana.pressure_unit)
        u = self.cal_abs_digit_uncert(p_ind, self.resolution)

        ana.store("Uncertainty", "digit", u/p_ind, "1")
