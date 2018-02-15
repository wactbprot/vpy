import numpy as np
import sympy as sym
from .std import Se3
from ...vpy_io import Io

class Cal(Se3):

    def __init__(self, doc):
        super().__init__(doc)

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

        ..todo::
            pressure_nd is alien here--> move to the surface/scripts

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        p_nd_off = self.Pres.get_value("nd_offset", "mbar")
        p_nd_ind = self.Pres.get_value("nd_ind", "mbar")

        res.store("Pressure" ,"nd", p_nd_ind - p_nd_off , "mbar")

    def pressure_fill(self, res):
        """Calculates the mean value of the filling pressure by means of
        *GroupNormal* methods.

        Stores result under the path *Pressure, fill, mbar*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        val_conf_time = self.val_conf["Time"]["Fill"]
        aux_conf_time = self.aux_val_conf["Time"]["Offset"]
        val_conf      = self.val_conf["Pressure"]["Fill"]

        val_conf_targ = self.val_conf["Pressure"]["FillTarget"]
        aux_conf      = self.aux_val_conf["Pressure"]["Offset"]

        fill_time     = self.Time.get_value(val_conf_time["Type"],
                                            val_conf_time["Unit"])

        fill_target   = self.Pres.get_value(val_conf_targ["Type"],
                                            val_conf_targ["Unit"])

        N   = len(val_conf)
        M   = len(fill_target)

        cor_arr = []
        for i in range(N):
            FillDev = self.FillDevs[i]

            p_corr = np.full(self.no_of_meas_points, np.nan)
            val = val_conf[i]
            aux = aux_conf[i]

            ind = self.Pres.get_value(val["Type"], val["Unit"])
            off = self.Aux.get_val_by_time(fill_time, aux_conf_time["Type"],
                                                        aux_conf_time["Unit"],
                                                        aux["Type"],
                                                        aux["Unit"])
            p   = ind - off

            e       = FillDev.get_error_interpol(p, self.unit)

            p_corr = p/(e + 1.0)
            cor_arr.append(p_corr)
            ldevname = FillDev.get_name().lower()
            res.store("Pressure" ,"{}-fill".format(ldevname), p_corr , val["Unit"])
            res.store("Pressure" ,"{}-fill_offset".format(ldevname), off, val["Unit"])

        rsh_corr_arr = np.reshape(cor_arr, (N, M))
        p_mean       = np.nanmean(rsh_corr_arr, axis=0)

        def cnt_nan(d):
            return np.count_nonzero(~np.isnan(d))

        p_std        = np.nanstd(rsh_corr_arr, axis=0)
        n            = np.apply_along_axis(cnt_nan, 0, rsh_corr_arr)
        
        res.store("Pressure" ,"fill",p_mean, val["Unit"], p_std, n)

        #p_arr     = p_ind_arr - p_off_arr
        #e_arr     = self.GN.get_error_iterpol(p_arr, "mbar")
        #p_fill    = self.GN.cal_mean_pressure(p_cor_arr, "mbar" )

        #res.store("Pressure" ,"fill", p_fill , "mbar")

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

        i_s = np.where(f == "f_s")[0]
        i_m = np.where(f == "f_m")[0]
        i_l = np.where(f == "f_l")[0]

        if len(i_s) > 0:
            t[i_s] = self.temperature_volume_s()[i_s]
            self.log.info("Points {}  belong to f_s".format(i_s[0]))

        if len(i_m) > 0:
            t[i_m] = self.temperature_volume_m()[i_m]
            self.log.info("Points {}  belong to f_m".format(i_m[0]))

        if len(i_l) > 0:
            t[i_l] = self.temperature_volume_l()[i_l]
            self.log.info("Points {}  belong to f_l".format(i_l[0]))

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

    def temperature_volume_s(self):
        """Temperature of the medium (0.02l) volume. The used  sensors are:

        *channel 3001 to 3003*

        .. note::

            range(3001,3004) becomes  3001 to 3003
        """

        chs     = list(range(3001, 3004))
        tem_arr = self.Temp.get_array("ch_", chs, "_before", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)

    def temperature_volume_m(self):
        """Temperature of the medium (0.2l) volume. The used  sensors are:

        *channel 3004 to 3013*
        """
        chs     = list(range(3004, 3014))
        tem_arr = self.Temp.get_array("ch_", chs, "_before", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)

    def temperature_volume_l(self):
        """Temperature of the medium (0.2l) volume. The used  sensors are:

        *channel 3014 to 3030*
        """
        chs     = list(range(3014, 3031))
        tem_arr = self.Temp.get_array("ch_", chs, "_before", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)

    def temperature_vessel(self):
        """Temperature of the medium (0.2l) volume. The used  sensors are:

        *channel 1001 to 1030* and *channel 2001 to 2028*
        """
        chs = list(range(1001, 1031)) + list(range(2001, 2029))

        tem_arr = self.Temp.get_array("ch_", chs, "_after", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)

    def temperature_room(self, res):
        """Calculates the temperature of the room.
        """
        tem = self.temperature_foe24()
        res.store("Temperature","room", tem , "K")

    def temperature_foe24(self):
        """Temperature of the room. The used  sensors are:

        *channel 2029 to 2030*
        """
        chs = list(range(2029, 2031))

        tem_arr = self.Temp.get_array("ch_", chs, "_before", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)
