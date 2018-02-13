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
        ind_1000      = []
        off_1000      = []
        val_conf_1000 = self.val_conf["Pressure"]["1000TorrFill"]
        aux_conf_1000 = self.aux_val_conf["Pressure"]["1000TorrFillOffset"]
        
        for val in val_conf_1000:
            ind_1000.append(self.Pres.get_value(val["Type"], val["Unit"]))

        #chs = [
        #    "1T_1","1T_2","1T_3",
        #    "10T_1","10T_2","10T_3",
        #    "100T_1","100T_2","100T_3",
        #    "1000T_1","1000T_2","1000T_3"
        #    ]
        #N = len(chs)

        #p_ind_arr = self.Pres.get_array("", chs, "-fill","mbar")
        #meas_time = self.Time.get_value("amt_fill", "ms")

        #for i in range(N):
        #    chnm = "{}-offset".format(chs[i])
        #    vec  = self.Aux.get_val_by_time(meas_time, "offset_mt", "ms", chnm, "mbar")
        #    M    = len(vec)

        #    if i == 0:
        #        p_off_arr = np.full((N, M), np.nan)

        #    p_off_arr[i][:] = vec[:]

        #p_arr     = p_ind_arr - p_off_arr
        #e_arr     = self.GN.get_error_iterpol(p_arr, "mbar")
        #p_cor_arr = p_arr/(e_arr + 1.0)
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
