import numpy as np
import sympy as sym
from .std import Se3

class Cal(Se3):

    def __init__(self, doc):
        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def pressure_cal(self, res):
        """Calculates the calibration pressure by means of defined model

        Stores result under the path *Pressure, cal, mbar*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        self.define_model()
        self.get_add_ratio(res)
        self.pressure_fill(res)
        self.temperature_before(res)
        self.temperature_after(res)
        self.real_gas_correction(res)
        self.gen_val_array(res)

        p_cal = sym.lambdify(self.symb, self.model, "numpy")(*self.val_arr)

        res.store("Pressure" ,"cal", p_cal, self.unit)

    def get_add_ratio(self, res):
        """ Calculates the pressure ratio measured during
        the estimation of additional volume and stores it
        below ``Ratio``

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        """

        p_before = self.Aux.get_value("add_before", "V")
        p_after  = self.Aux.get_value("add_after","V")
        if p_before is None and p_after is None:
            r_add = 0.0
            self.log.warn("No additional Volume, r_add becomes 0.0")
        else:
            r_add = np.nanmean(p_after/(p_before - p_after))

        res.store("Ratio" ,"add", np.full(self.no_of_meas_points, r_add), "1")

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

        .. todo::

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
        """Calculates the singel and mean value of the filling pressure
        by means data in values.json

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
        M   = self.no_of_meas_points

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
            e   = FillDev.get_error_interpol(p, self.unit, fill_target, self.unit)

            p_corr = p/(e + 1.0)
            cor_arr.append(p_corr)
            ldevname = FillDev.get_name().lower()
            res.store("Pressure" ,"{}-fill".format(ldevname), p_corr , val["Unit"])
            res.store("Pressure" ,"{}-fill_offset".format(ldevname), off, val["Unit"])

        p_mean  = np.nanmean(cor_arr, axis=0)

        def cnt_nan(d):
            return np.count_nonzero(~np.isnan(d))

        p_std        = np.nanstd(cor_arr, axis=0)
        n            = np.apply_along_axis(cnt_nan, 0, cor_arr)

        res.store("Pressure" ,"fill", p_mean, val["Unit"], p_std, n)

    def temperature(self, channels, sufix="_before", prefix="ch_", sufix_corr="", prefix_corr= "corr_ch_"):
        tem_arr = self.Temp.get_array(prefix, channels, sufix, "C")
        cor_arr = self.TDev.get_array(prefix_corr, channels, sufix_corr, "K")

        conv    = self.Cons.get_conv("C", "K")
        t_m = np.mean(tem_arr + cor_arr + conv, axis=0)
        t_s = np.std(tem_arr + cor_arr + conv, axis=0)

        return t_m, t_s, len(channels)

    def temperature_before(self, res):
        """Calculates the temperature of the starting volumes.

        Stores result under the path  *Temperature, before, K*
        For the temperature of the medium (0.02l) volume the used  sensors are:
        *channel 3001 to 3003*
        For the temperature of the medium (0.2l) volume the used  sensors are:
        *channel 3004 to 3013*
        For the temperature of the large (2l) volume the used  sensors are:
        *channel 3014 to 3030*


        .. todo::

            use shape() instead of len()

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f   = self.get_expansion()
        t_mean  = np.full(self.no_of_meas_points, np.nan)
        t_stdv  = np.full(self.no_of_meas_points, np.nan)
        t_N     = np.full(self.no_of_meas_points, np.nan)

        i_s = np.where(f == "f_s")[0]
        i_m = np.where(f == "f_m")[0]
        i_l = np.where(f == "f_l")[0]

        if len(i_s) > 0:
            self.log.info("Points {}  belong to f_s".format(i_s))
            t_m, t_s, N = self.temperature(list(range(3001, 3004)))
            t_mean[i_s] = t_m[i_s]
            t_stdv[i_s] = t_s[i_s]
            t_N[i_s] = N

        if len(i_m) > 0:
            self.log.info("Points {}  belong to f_m".format(i_m))
            t_m, t_s, N = self.temperature(list(range(3004, 3014)))
            t_mean[i_m] = t_m[i_m]
            t_stdv[i_m] = t_s[i_m]
            t_N[i_m] = N

        if len(i_l) > 0:
            self.log.info("Points {}  belong to f_l".format(i_l))
            t_m, t_s, N = self.temperature(list(range(3014, 3031)))
            t_mean[i_l] = t_m[i_l]
            t_stdv[i_l] = t_s[i_l]
            t_N[i_l] = N

        res.store("Temperature" ,"before", t_mean , "K", t_stdv, t_N)

    def temperature_after(self, res):
        """Calculates the temperature of the end volume.
        Stores result under the path *Temperature, after, K*
        The used  sensors are:
        *channel 1001 to 1030* and *channel 2001 to 2028*
        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        t_mean, t_stdv, t_N = self.temperature(list(range(1001, 1031)) + list(range(2001, 2029)), "_after")
        res.store("Temperature","after", t_mean , "K", t_stdv, t_N)

    def temperature_room(self, res):
        """Calculates the temperature of the room.
        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        t_mean, t_stdv, t_N = self.temperature(list(range(2029, 2031)), "_after")
        res.store("Temperature","room", t_mean , "K", t_stdv, t_N)
