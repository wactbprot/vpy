import numpy as np
import sympy as sym
import inspect as insp

from .std import Se2
from ...vpy_io import Io

class Cal(Se2):

    def __init__(self, doc):
        super().__init__(doc)

    def time(self, res):
        """Calculates  time axis
        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv = self.Cons.get_conv("ms", "h")
        t = self.Time.get_rmt("amt_fill", "ms")*conv

        res.store("Time" ,"rmt", t , "h")


    def get_expansion(self):
        """Returns an np.array containing
        the expansion name (``f_s``, ``f_m`` or ``f_l``)
        of the length: ``self.no_of_meas_points```

        :returns: array of expansion names
        :rtype: np.array of strings
        """
        f = self.Aux.get_expansion()
        if f is not None:
            return np.full(self.no_of_meas_points, f)

    def pressure_nd(self, res):
        """Stores the differential pressure of the zero
         under the path  *Pressure, nd, mbar*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        p_nd_off = self.Pres.get_value("nd_offset", "mbar")
        p_nd_ind = self.Pres.get_value("nd_ind", "mbar")

        res.store("Pressure" ,"nd", p_nd_ind - p_nd_off , "mbar")

    def pressure_fill(self, res):
        """Calculates the mean value of the filling pressure


        Stores result under the path *Pressure, fill, mbar*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        conv    = self.Cons.get_conv("kPa", "mbar")

        p_fill        = self.Pres.get_value("fill","kPa")*conv
        meas_time     = self.Time.get_value("amt_fill", "ms")
        p_fill_offset = self.Aux.get_val_by_time(meas_time, "offset_mt", "ms", "fill_offset", "kPa")*conv

        p_fill_uncorr = (p_fill  - p_fill_offset)
        e             = self.Qbs.get_error_correction(p_fill_uncorr, "mbar", "%")/100.
        pfill         = p_fill_uncorr/(e + 1.)

        res.store("Error" ,"fill", e, "1")
        res.store("Pressure" ,"fill_offset", p_fill_offset, "mbar")
        res.store("Pressure" ,"fill", p_fill, "mbar")


    def temperature_before(self, res):
        """Calculates the temperature of the starting volumes.

        Stores result under the path  *Temperature, before, K*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f   = self.get_expansion()
        t   = np.full(self.no_of_meas_points, np.nan)

        i_1 = np.where(f == "f_1")[0]
        i_2 = np.where(f == "f_2")[0]

        if len(i_1) > 0:
            t[i_1] = self.temperature_volume_1()[i_1]
            self.log.info("Points {}  belong to f_1".format(i_1[0]))

        if len(i_2) > 0:
            t[i_2] = self.temperature_volume_2()[i_2]
            self.log.info("Points {}  belong to f_2".format(i_2[0]))

        res.store("Temperature" ,"before", t , "K")

    def temperature_after(self, res):
        """Calculates the temperature of the end volume.
        Stores result under the path *Temperature, after, K*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        tem = self.temperature_vessel()
        res.store("Temperature","after", tem , "K")

    def temperature_volume_2(self):
        """Temperature of the medium (0.1l) volume. The used  sensors are:

        *channel 101*

        """
        conv    = self.Cons.get_conv("C", "K")

        chs     = list(range(101, 102))
        tem_arr = self.Temp.get_array("keithley_T_before_ch", chs, "", "C")
        cor_arr = self.TDev.get_array("corr_keithleych", chs, "", "K")

        t_mean =  np.mean(tem_arr + cor_arr + conv, axis=0)

        chs_add     = list(range(101, 103))
        tem_arr_add = self.Temp.get_array("agilent_T_before_ch", chs, "", "C")
        cor_arr_add = self.TDevAdd.get_array("agilentCorrCh", chs, "", "K")

        t_mean_add =  np.mean(tem_arr_add + cor_arr_add + conv, axis=0)

        return (t_mean + t_mean_add)/2.

    def temperature_volume_1(self):
            """Temperature of the medium (0.1l) volume. The used  sensors are:

            *channel 101*

            """
            conv    = self.Cons.get_conv("C", "K")

            chs     = list(range(102, 104))
            tem_arr = self.Temp.get_array("keithley_T_before_ch", chs, "", "C")
            cor_arr = self.TDev.get_array("corr_keithleych", chs, "", "K")

            t_mean =  np.mean(tem_arr + cor_arr + conv, axis=0)

            chs_add     = list(range(103, 105))
            tem_arr_add = self.Temp.get_array("agilent_T_before_ch", chs, "", "C")
            cor_arr_add = self.TDevAdd.get_array("agilentCorrCh", chs, "", "K")

            t_mean_add =  np.mean(tem_arr_add + cor_arr_add + conv, axis=0)

            return (t_mean + t_mean_add)/2.



    def temperature_vessel(self):
        """Temperature of 100l vessel. The used  sensors are:

        *ch 105 .. 110*
        """
        conv    = self.Cons.get_conv("C", "K")

        chs     = list(range(105, 111))
        tem_arr = self.Temp.get_array("keithley_T_after_ch", chs, "", "C")
        cor_arr = self.TDev.get_array("corr_keithleych", chs, "", "K")

        t_mean =  np.mean(tem_arr + cor_arr + conv, axis=0)

        chs_add     = list(range(105, 111))
        tem_arr_add = self.Temp.get_array("agilent_T_after_ch", chs, "", "C")
        cor_arr_add = self.TDevAdd.get_array("agilentCorrCh", chs, "", "K")

        t_mean_add =  np.mean(tem_arr_add + cor_arr_add + conv, axis=0)


        return (t_mean + t_mean_add)/2.
