import numpy as np
import sympy as sym
from datetime import datetime
from .std import Se3


class Cal(Se3):

    def __init__(self, doc):
        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def check(self, res, chk):
        """ Checks the measured state values against a given
        min/max-list (stored in ``vpy/standard/[.]/state.json``).
        Calculates a rating for each value. The range for
        this value is [0..9] where 0 is (mostly) best and 9 is (mostly) worst.

        :param: res Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to pick the values from
        :type: class

        :param: chc Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to store the values in
        :type: class
        """
        sc_dict = self.state_check
        amt = self.Time.get_value("amt", "ms")
        dt =[]
        for d in amt:
            d = int(d)/1000.0
            dt.append(datetime.fromtimestamp(d).strftime('%Y-%m-%d %H:%M:%S'))


        for quant in sc_dict:  # m ... Temperature ect.
            for head in sc_dict[quant]:  # ... VesselBranch
                if isinstance(sc_dict[quant][head], dict):
                    dct = sc_dict[quant][head]

                    val = res.pick(quant, dct['Type'], dct['Unit'])
                    rnd_val = []
                    rtn_val =[]
                    min = dct['Min']
                    max = dct['Max']

                    v_vec = np.linspace(min, max, 10)
                    r_vec = np.linspace(0, 9, 10)

                    for v in val:
                        rnd_val.append('{:0.3e}'.format(v))
                        if v < min:
                            rtn_val.append(0)
                        elif v > max:
                            rtn_val.append(9)
                        else:
                            d = np.abs(v_vec - v)
                            i = np.argmin(d)
                            rtn_val.append(r_vec[i])

                    dct['Value'] = rnd_val
                    dct['Rating'] = rtn_val
                    dct['Date'] = dt
                    chk.store_dict(quant, dct)

    def outgas_rate(self, res):
        """ Calculates the outgasing rate of  dut-a,b,c u (vacuum branch
        with dut valves closed) and v (vessel only). If the pressure rise is
        uncorrelated the minimum outgasing rate of the vessel plus 20% is used as an
        replace value.

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        R_min = 0.99

        sc_dict = self.state_check
        m_min = sc_dict['OutGasRate']['Vessel']['Min']
        m_max = sc_dict['OutGasRate']['Vessel']['Max']
        m_med = m_min * (1 + 0.2)
        conv = self.Cons.get_conv("ms", "s")

        m_abc = self.OutGas.get_value("rise_abc_slope_x", "mbar/ms") / conv
        R_abc = self.OutGas.get_value("rise_abc_R", "1")
        i = (R_abc < R_min)
        if len(i) > 0:
            m_abc[i] = m_med

        m_bc = self.OutGas.get_value("rise_bc_slope_x", "mbar/ms") / conv
        R_bc = self.OutGas.get_value("rise_bc_R", "1")
        i = (R_bc < R_min)
        if len(i) > 0:
            m_bc[i] = m_med

        m_c = self.OutGas.get_value("rise_c_slope_x", "mbar/ms") / conv
        R_c = self.OutGas.get_value("rise_c_R", "1")
        i = (R_c < R_min)
        if len(i) > 0:
            m_c[i] = m_med

        m_u = self.OutGas.get_value("rise_u_slope_x", "mbar/ms") / conv
        R_u = self.OutGas.get_value("rise_u_R", "1")
        i = (R_u < R_min)
        if len(i) > 0:
            m_u[i] = m_med

        m_v = self.OutGas.get_value("rise_base_slope_x", "mbar/ms") / conv
        R_v = self.OutGas.get_value("rise_base_R", "1")
        i = (R_v < R_min)
        if len(i) > 0:
            m_v[i] = m_med

        m_b = m_bc - m_c
        m_a = m_abc - m_bc

        res.store("OutGasRate", "outgas_a",  m_a, "mbar/s")
        res.store("OutGasRate", "outgas_b",  m_b, "mbar/s")
        res.store("OutGasRate", "outgas_c",  m_c, "mbar/s")
        res.store("OutGasRate", "outgas_u",  m_u, "mbar/s")
        res.store("OutGasRate", "outgas_v",  m_v, "mbar/s")

    def temperatur_single(self, res):
        """ Adds the correction factor for each sensor and stores the result.

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        L = list(range(1001, 1031)) + list(range(2001, 2031)) + \
            list(range(3001, 3031))
        for ch in L:
            t_mean, t_stdv, t_N = self.temperature([ch], "state")

            res.store("Temperature", "ch_{}state".format(ch), t_mean, "K")

    def pressure_state(self, res):
        """ So far: a simple tarnsfer of measured values to
        Analysis section.

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        # more dry pls
        res.store("Pressure", "1T_1-state", self.Pres.get_value("1T_1-state", "mbar"), "mbar")
        res.store("Pressure", "1T_2-state", self.Pres.get_value("1T_2-state", "mbar"), "mbar")
        res.store("Pressure", "1T_3-state", self.Pres.get_value("1T_3-state", "mbar"), "mbar")
        res.store("Pressure", "10T_1-state", self.Pres.get_value("10T_1-state", "mbar"), "mbar")
        res.store("Pressure", "10T_2-state", self.Pres.get_value("10T_2-state", "mbar"), "mbar")
        res.store("Pressure", "10T_3-state", self.Pres.get_value("10T_3-state", "mbar"), "mbar")
        res.store("Pressure", "100T_1-state", self.Pres.get_value("100T_1-state", "mbar"), "mbar")
        res.store("Pressure", "100T_2-state", self.Pres.get_value("100T_2-state", "mbar"), "mbar")
        res.store("Pressure", "100T_3-state", self.Pres.get_value("100T_3-state", "mbar"), "mbar")
        res.store("Pressure", "1000T_1-state", self.Pres.get_value("1000T_1-state", "mbar"), "mbar")
        res.store("Pressure", "1000T_2-state", self.Pres.get_value("1000T_2-state", "mbar"), "mbar")
        res.store("Pressure", "1000T_3-state", self.Pres.get_value("1000T_3-state", "mbar"), "mbar")

    def volume_add(self, res):
        """ Calculates additional volumes of dut-a,b,c branch of state
        measurement documents.


        .. math::

            V_{add} = V_5 \\frac{p_{after}}{p_{before} - p_{after}}

        Stores result under the path *Volume, add_x, cm^3*

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        V_5 = self.get_value("V_5", "cm^3")
        p_before = self.Pres.get_value("add_vol_before", "mbar")
        p_before_a = self.Pres.get_value("add_vol_a_before", "mbar")
        p_before_ab = self.Pres.get_value("add_vol_ab_before", "mbar")
        p_before_abc = self.Pres.get_value("add_vol_abc_before", "mbar")

        p_after = self.Pres.get_value("add_vol_after", "mbar")
        p_after_a = self.Pres.get_value("add_vol_a_after", "mbar")
        p_after_ab = self.Pres.get_value("add_vol_ab_after", "mbar")
        p_after_abc = self.Pres.get_value("add_vol_abc_after", "mbar")

        V_add = V_5 * p_after / (p_before - p_after)
        V_add_a = V_5 * p_after_a / (p_before_a - p_after_a)
        V_add_ab = V_5 * p_after_ab / (p_before_ab - p_after_ab)
        V_add_abc = V_5 * p_after_abc / (p_before_abc - p_after_abc)

        V_a = V_add_a - V_add
        V_b = V_add_ab - V_add - V_a
        V_c = V_add_abc - V_add - V_a - V_b

        V_add_bc = V_add + V_b + V_c
        V_add_c = V_add + V_c

        res.store("Volume", "add_branch",   V_add, "cm^3")

        res.store("Volume", "add_a",   V_add_a, "cm^3")
        res.store("Volume", "add_ab",  V_add_ab, "cm^3")
        res.store("Volume", "add_abc", V_add_abc, "cm^3")
        res.store("Volume", "add_bc",   V_add_bc, "cm^3")
        res.store("Volume", "add_c",  V_add_c, "cm^3")

        res.store("Volume", "a",   V_a, "cm^3")
        res.store("Volume", "b",   V_b, "cm^3")
        res.store("Volume", "c",   V_c, "cm^3")

    def pressure_cal(self, res):
        """Calculates the calibration pressure by means of defined model

        Stores result under the path *Pressure, cal, mbar*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        self.define_model()
        self.pressure_fill(res)
        self.temperature_before(res)
        self.temperature_after(res)
        self.real_gas_correction(res)
        self.gen_val_array(res)

        p_cal = sym.lambdify(self.symb, self.model, "numpy")(*self.val_arr)

        res.store("Pressure", "cal", p_cal, self.unit)

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

        res.store("Pressure", "nd", p_nd_ind - p_nd_off, "mbar")

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
        val_conf = self.val_conf["Pressure"]["Fill"]

        val_conf_targ = self.val_conf["Pressure"]["FillTarget"]
        aux_conf = self.aux_val_conf["Pressure"]["Offset"]

        fill_time = self.Time.get_value(val_conf_time["Type"],
                                        val_conf_time["Unit"])

        fill_target = self.Pres.get_value(val_conf_targ["Type"],
                                          val_conf_targ["Unit"])

        N = len(val_conf)
        M = self.no_of_meas_points

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
            p = ind - off
            e = FillDev.get_error_interpol(
                p, self.unit, fill_target, self.unit)

            p_corr = p / (e + 1.0)
            cor_arr.append(p_corr)
            ldevname = FillDev.get_name().lower()
            res.store("Pressure", "{}-fill".format(ldevname),
                      p_corr, val["Unit"])
            res.store("Pressure", "{}-fill_offset".format(ldevname),
                      off, val["Unit"])

        p_mean = np.nanmean(cor_arr, axis=0)

        def cnt_nan(d):
            return np.count_nonzero(~np.isnan(d))

        p_std = np.nanstd(cor_arr, axis=0)
        n = np.apply_along_axis(cnt_nan, 0, cor_arr)

        res.store("Pressure", "fill", p_mean, val["Unit"], p_std, n)

    def temperature(self, channels, sufix="_before", prefix="ch_", sufix_corr="", prefix_corr="corr_ch_"):
        tem_arr = self.Temp.get_array(prefix, channels, sufix, "C")
        cor_arr = self.TDev.get_array(prefix_corr, channels, sufix_corr, "K")

        conv = self.Cons.get_conv("C", "K")
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
        f = self.get_expansion()
        t_mean = np.full(self.no_of_meas_points, np.nan)
        t_stdv = np.full(self.no_of_meas_points, np.nan)
        t_N = np.full(self.no_of_meas_points, np.nan)

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

        res.store("Temperature", "before", t_mean, "K", t_stdv, t_N)

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

        t_mean, t_stdv, t_N = self.temperature(
            list(range(1001, 1031)) + list(range(2001, 2029)), "_after")
        res.store("Temperature", "after", t_mean, "K", t_stdv, t_N)

    def temperature_room(self, res):
        """Calculates the temperature of the room.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        t_mean, t_stdv, t_N = self.temperature(
            list(range(2029, 2031)), "_after")
        res.store("Temperature", "room", t_mean, "K", t_stdv, t_N)
