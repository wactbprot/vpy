import numpy as np
import sympy as sym
from datetime import datetime
from .std import Se3


class Cal(Se3):

    def __init__(self, doc):
        super().__init__(doc)
    
    def check_analysis(self, res, chk):
        pass

        
    def check_state(self, res, chk):
        """ Checks the measured state values against a given
        min/max-list (stored in ``self.state_check``).
        Calculates a rating for each value. The range for
        this value is [0..9] where 0 is (mostly) best and 9 is (mostly) worst.

        :param: res instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to pick the values from
        :type: class

        :param: chc instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to store the values in
        :type: class
        """
        sc_dict = self.state_check
        amt = self.Time.get_value("amt", "ms")
        dt = []
        for d in amt:
            d = int(d) / 1000.0
            dt.append(datetime.fromtimestamp(d).strftime('%Y-%m-%d %H:%M:%S'))

        for quant in sc_dict:  # m ... Temperature ect.
            for head in sc_dict[quant]:  # ... VesselBranch
                if isinstance(sc_dict[quant][head], dict):
                    dct = sc_dict[quant][head]

                    val = res.pick(quant, dct['Type'], dct['Unit'])
                    rnd_val = []
                    rtn_val = []
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

    def outgas_state(self, res):
        """ Calculates the outgasing rate of dut-a,b,c u (vacuum branch
        with dut valves closed) and v (vessel only).

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        conv = self.Cons.get_conv("ms", "s")

        m_abc = self.OutGas.get_value("rise_abc_slope_x", "mbar/ms") / conv
        m_bc = self.OutGas.get_value("rise_bc_slope_x", "mbar/ms") / conv
        m_c = self.OutGas.get_value("rise_c_slope_x", "mbar/ms") / conv
        m_u = self.OutGas.get_value("rise_u_slope_x", "mbar/ms") / conv
        m_v = self.OutGas.get_value("rise_base_slope_x", "mbar/ms") / conv

        res.store("OutGasRate", "outgas_abc",  m_abc, "mbar/s")
        res.store("OutGasRate", "outgas_bc",  m_bc, "mbar/s")
        res.store("OutGasRate", "outgas_c",  m_c, "mbar/s")
        res.store("OutGasRate", "outgas_u",  m_u, "mbar/s")
        res.store("OutGasRate", "outgas_v",  m_v, "mbar/s")

    def temperature_state(self, res):
        """ Adds the correction factor for each sensor and stores the result.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        L = list(range(1001, 1031)) + list(range(2001, 2031)) + \
            list(range(3001, 3031))
        for ch in L:
            t_mean, _, _ = self.temperature([ch], "state")

            res.store("Temperature", "ch_{}state".format(ch), t_mean, "K")

    def time_state(self, res):
        """A transfer of absolute measure time to 
        relative measure time and stores the result in analysis section.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        t = self.Time.get_rmt(dict_type="amt", unit="ms")
        conv2s = self.Cons.get_conv(from_unit="ms", to_unit="s")
        conv2min = self.Cons.get_conv(from_unit="s", to_unit="min")
        
        res.store("Time", "amt", t *conv2s*conv2min, "ms")
    
    def pressure_state(self, res):
        """ So far: a simple transfer of measured values to
        Analysis section.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        self.log.debug("transfer state pressure")
        for state_type in self.state_types:
            p = self.Pres.get_value("1T_1-state", self.unit)
            res.store("Pressure", state_type, p, self.unit)

    def volume_state(self, res):
        """ Calculates additional volumes of dut-a,b,c branch of state
        measurement documents.


        .. math::

            V_{add} = V_5 \\frac{p_{after}}{p_{before} - p_{after}}

        Stores result under the path *Volume, add_x, cm^3*

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        V_5 = self.get_value("V_5", "cm^3")
        p_before = self.Pres.get_value("add_vol_before", self.unit)
        p_before_a = self.Pres.get_value("add_vol_a_before", self.unit)
        p_before_ab = self.Pres.get_value("add_vol_ab_before", self.unit)
        p_before_abc = self.Pres.get_value("add_vol_abc_before", self.unit)

        p_after = self.Pres.get_value("add_vol_after", self.unit)
        p_after_a = self.Pres.get_value("add_vol_a_after", self.unit)
        p_after_ab = self.Pres.get_value("add_vol_ab_after", self.unit)
        p_after_abc = self.Pres.get_value("add_vol_abc_after", self.unit)

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

    def volume_start(self, res):
        """Builds a vector containing the start volume and stores it.

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        vol = np.full(self.no_of_meas_points, np.nan)
        f_name = self.get_expansion_name()

        i_s = np.where(f_name == "f_s")
        i_m = np.where(f_name == "f_m")
        i_l = np.where(f_name == "f_l")

        if np.shape(i_s)[1] > 0:
            vol[i_s] = self.get_value("V_s", "cm^3")
        if np.shape(i_m)[1] > 0:
            vol[i_m] = self.get_value("V_m", "cm^3")
        if np.shape(i_l)[1] > 0:
            vol[i_l] = self.get_value("V_l", "cm^3")

        res.store("Volume", "start",   vol, "cm^3")

    def volume_add(self, res):
        """Builds up a vector containing the additional volume and stores it.
        The additional volumes should be measured and analyzed before and stored
        under *Analysis.AuxValues.Volumes*. So far, the last measured values *[-1]*
        are used. 

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """


        vol_add_branch = res.pick('Volume', dict_type='add_branch', dict_unit='cm^3', dest='AuxValues')[-1]
        vol_a = res.pick('Volume', dict_type='a', dict_unit='cm^3', dest='AuxValues')[-1]
        vol_b = res.pick('Volume', dict_type='b', dict_unit='cm^3', dest='AuxValues')[-1]
        vol_c = res.pick('Volume', dict_type='c', dict_unit='cm^3', dest='AuxValues')[-1]
        
        dut_a = self.Pos.get_str('dut_a')
        dut_b = self.Pos.get_str('dut_b')
        dut_c = self.Pos.get_str('dut_c')

        vol = np.full(self.no_of_meas_points, vol_add_branch)

        i_a = np.where(dut_a == "open")
        i_b = np.where(dut_b == "open")
        i_c = np.where(dut_c == "open")

        
        if np.shape(i_a)[1] > 0:
            vol[i_a] = vol[i_a] + vol_a
        if np.shape(i_b)[1] > 0:
            vol[i_b] = vol[i_a] + vol_b
        if np.shape(i_c)[1] > 0:
            vol[i_c] = vol[i_c] + vol_c

        res.store("Volume", "add",   vol, "cm^3")
    
    def error(self, res):
        """Calculates the error of indication from the calibration pressure and 
        the corrected indicated pressure.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        ind = res.pick("Pressure", "ind_corr",self.unit)
        cal = res.pick("Pressure", "cal",self.unit)
        
        res.store('Error', 'relative', ind/cal-1, '1')

    def pressure_ind(self, res):
        """Calculates the corrected indicated pressure in dependence
         of the customer device. *offset*  and uncorrected *ind*ication are also stored.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        gas = self.Aux.get_gas()

        temperature_dict = res.pick_dict('Temperature', 'after')
        offset_dict = self.Pres.get_dict('Type', 'ind_offset' )    
        ind_dict = self.Pres.get_dict('Type', 'ind' )

        offset = self.CustomerDevice.pressure(offset_dict, temperature_dict, unit = self.unit, gas=gas)
        ind = self.CustomerDevice.pressure(ind_dict, temperature_dict, unit = self.unit, gas=gas)
        
        res.store("Pressure", "offset", offset, self.unit)
        res.store("Pressure", "ind", ind, self.unit)
        res.store("Pressure", "ind_corr", ind - offset, self.unit)
        self.log.debug("indicated pressure in {} is: {}".format(self.unit, ind))
    
    def pressure_cal(self, res):
        """Calculates the calibration pressure nand stores the
        result under the path *Pressure, cal, mbar*

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        ## removed implicit pfill etc. calculation
        
        p_fill = res.pick("Pressure", "fill", self.unit)
        self.log.debug("filling pressure is: {}".format(p_fill))

        rg = res.pick("Correction", "rg", "1")
        self.log.debug("real gas correctioin is: {}".format(rg))
        
        f = res.pick("Expansion", "uncorr", "1")
        self.log.debug("expansion factor is: {}".format(f))

        T_before = res.pick("Temperature", "before", "K")
        self.log.debug("Temperature before is: {}".format(T_before))

        T_after = res.pick("Temperature", "after", "K")
        self.log.debug("Temperature after is: {}".format(T_after))

        V_add = res.pick("Volume", "add", "cm^3")
        self.log.debug("Volume add is: {}".format(V_add))

        V_start = res.pick("Volume", "start", "cm^3")
        self.log.debug("Volume start is: {}".format(V_start))

        p_cal = p_fill / rg * T_after / T_before / (1.0 / f + V_add / V_start)
        self.log.debug("calibration pressure in {} is: {}".format(self.unit, p_cal))
        
        res.store("Pressure", "cal", p_cal, self.unit)

    def pressure_fill(self, res):
        """Calculates the  mean value of the filling pressure.
        Stores result under the path *Pressure, fill, Pa*

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        self.log.debug("start filling pressure")


        fill_time = self.Time.get_value("amt_fill", "ms")
        fill_target = self.Pres.get_value("target_fill", self.unit)

        N = len(self.fill_types)

        cor_arr = []
        for i in range(N):
            FillDev = self.FillDevs[i]
            self.log.debug("Working on filling pressure of device {}".format(FillDev.name))
            p_corr = np.full(self.no_of_meas_points, np.nan)

            ind = self.Pres.get_value(self.fill_types[i], self.unit)
            off = self.Aux.get_val_by_time(
                fill_time, "offset_mt", "ms", self.offset_types[i], self.unit)

            p = ind - off
            e = FillDev.get_error_interpol(p, self.unit, fill_target, self.unit)
           
            p_corr = p / (e + 1.0)
            cor_arr.append(p_corr)

        p_mean = np.nanmean(cor_arr, axis=0)
       
        def cnt_nan(d):
            return np.count_nonzero(~np.isnan(d))

        p_std = np.nanstd(cor_arr, axis=0)
        n = np.apply_along_axis(cnt_nan, 0, cor_arr)

        res.store("Pressure", "fill", p_mean, self.unit, p_std, n)

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

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f_name = self.get_expansion_name()
        t_mean = np.full(self.no_of_meas_points, np.nan)
        t_stdv = np.full(self.no_of_meas_points, np.nan)
        t_N = np.full(self.no_of_meas_points, np.nan)

        i_s = np.where(f_name == "f_s")
        i_m = np.where(f_name == "f_m")
        i_l = np.where(f_name == "f_l")

        if np.shape(i_s)[1] > 0:
            self.log.info("Points {}  belong to f_s".format(i_s))
            t_m, t_s, N = self.temperature(list(range(3001, 3004)))
            t_mean[i_s] = t_m[i_s]
            t_stdv[i_s] = t_s[i_s]
            t_N[i_s] = N

        if np.shape(i_m)[1] > 0:
            self.log.info("Points {}  belong to f_m".format(i_m))
            t_m, t_s, N = self.temperature(list(range(3004, 3014)))
            t_mean[i_m] = t_m[i_m]
            t_stdv[i_m] = t_s[i_m]
            t_N[i_m] = N

        if np.shape(i_l)[1] > 0:
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

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        t_mean, t_stdv, t_N = self.temperature(
            list(range(1001, 1031)) + list(range(2001, 2029)), "_after")
        res.store("Temperature", "after", t_mean, "K", t_stdv, t_N)

    def temperature_room(self, res):
        """Calculates the temperature of the room.

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        t_mean, t_stdv, t_N = self.temperature(
            list(range(2029, 2031)), "_after")
        res.store("Temperature", "room", t_mean, "K", t_stdv, t_N)
