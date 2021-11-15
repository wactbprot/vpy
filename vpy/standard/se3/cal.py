import numpy as np
import copy
import sympy as sym
from .std import Se3


class Cal(Se3):
    ## sd of the gn cdgs must be better than:
    gn_sd_threshold = 1e-2

    np.warnings.filterwarnings('ignore')

    def __init__(self, doc):
        super().__init__(doc)

    def check_analysis(self, res, chk):
        """ Checks the analysis values against a given
        min/max-list (stored in ``self.analysis_check``).
        Calculates a rating for each value.

        :param: res instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to pick the values from
        :type: class

        :param: chk instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to store the values in
        :type: class
        """

        dt = self.Time.amt_to_date("amt_fill", "ms")
        self.loop_check_dict(check=self.analysis_check, compare=res, date=dt, result=chk)

    def check_state(self, res, chk):
        """ Checks the measured state values against a given
        min/max-list (stored in ``self.state_check``).
        Calculates a rating for each value.

        :param: res instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to pick the values from
        :type: class

        :param: chk instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit) to store the values in
        :type: class
        """

        dt = self.Time.amt_to_date("amt", "ms")
        self.loop_check_dict(check=self.state_check, compare=res, date=dt, result=chk)

    def loop_check_dict(self, check, compare,  date, result):
        """Loops over the given ``check`` dict. Compares the entries witth ``compare``
        and writes the results plus date to ``result``

        """
        for quant in check:  # m ... Temperature ect.
            for head in check[quant]:  # ... VesselBranch
                if isinstance(check[quant][head], dict):
                    dct = check[quant][head]
                    val = compare.pick(quant, dct['Type'], dct['Unit'])
                    rnd_val = []
                    rtn_val = []
                    v_min = dct['Min']
                    v_max = dct['Max']

                    v_vec = np.linspace(v_min, v_max, 10)
                    if quant in self.rating_distributions:
                        r_vec = self.rating_distributions[quant]
                    else:
                        r_vec = self.rating_distributions['Fallback']

                    for v in val:

                        if np.isnan(v):
                            rtn_val.append("NaN")
                            rnd_val.append("NaN")
                        else:
                            rnd_val.append('{:0.4e}'.format(v))
                            if v < v_min:
                                rtn_val.append(9)
                            elif v > v_max:
                                rtn_val.append(9)
                            else:
                                d = np.abs(v_vec - v)
                                i = np.argmin(d)
                                rtn_val.append(r_vec[i])

                    dct['Value'] = rnd_val
                    dct['Rating'] = rtn_val
                    dct['Date'] = date

                    result.store_dict(quant, dct)

    def outgas_state(self, res):
        """ Calculates the outgasing rate of dut-a,b,c u (vacuum branch
        with dut valves closed) and v (vessel only). About 50% of the
        outgasing rate is caused by the ion gauge (IG) which  is
        switched of during the calibration. The factor ``outgas_correction``
        takes this into account.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        time_conv = self.Cons.get_conv("ms", "s")

        m_abc = self.OutGas.get_value("rise_abc_slope_x", "mbar/ms") / time_conv
        m_bc = self.OutGas.get_value("rise_bc_slope_x", "mbar/ms") / time_conv
        m_c = self.OutGas.get_value("rise_c_slope_x", "mbar/ms") / time_conv
        m_u = self.OutGas.get_value("rise_u_slope_x", "mbar/ms") / time_conv
        m_v = self.OutGas.get_value("rise_base_slope_x", "mbar/ms") / time_conv
        m_b = self.OutGas.get_value("rise_inlet_closed_outlet_open_slope_x", "mbar/ms") / time_conv
        m_is = self.OutGas.get_value("rise_pressure_inlet_slope_x", "mbar/ms") / time_conv
        m_os = self.OutGas.get_value("rise_pressure_outlet_slope_x", "mbar/ms") / time_conv

        res.store("OutGasRate", "outgas_abc",  m_abc, "mbar/s")
        res.store("OutGasRate", "outgas_bc",  m_bc, "mbar/s")
        res.store("OutGasRate", "outgas_c",  m_c, "mbar/s")
        res.store("OutGasRate", "outgas_u",  m_u, "mbar/s")
        res.store("OutGasRate", "outgas_v",  m_v, "mbar/s")
        res.store("OutGasRate", "outgas_vessel_starting_volumes",  m_b, "mbar/s")
        res.store("OutGasRate", "outgas_pressure_inlet",  m_is, "mbar/s")
        res.store("OutGasRate", "outgas_pressure_outlet",  m_os, "mbar/s")

    def pressure_loss(self, res):
        """ Calculates the pressure loss.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        time_conv = self.Cons.get_conv("ms", "s")
        l_s = self.PressureLoss.get_value("loss_slope_x", "mbar/ms") / time_conv
        res.store("PressureLoss", "gas_inlet",  l_s, "mbar/s")


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
            p = self.Pres.get_value(state_type, self.unit)
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
            vol[i_b] = vol[i_b] + vol_b
        if np.shape(i_c)[1] > 0:
            vol[i_c] = vol[i_c] + vol_c

        res.store("Volume", "add",   vol, "cm^3")


    def deviation_target_fill(self, res):
        """Calculates the relative deviation from the target
        filling pressure.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        target_fill = self.Pres.get_value('target_fill', 'Pa')
        pressure_fill = res.pick('Pressure', 'fill', 'Pa')

        res.store('Error', 'dev_fill', pressure_fill/target_fill -1.0, '1')

    def deviation_target_cal(self, res):
        """Calculates the relative deviation between the target
        pressure and the calculated calibration pressure.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        target_cal = self.Pres.get_value('target_pressure', 'Pa')
        pressure_cal = res.pick('Pressure', 'cal', 'Pa')

        res.store('Error', 'dev_cal', pressure_cal/target_cal -1.0, '1')

    def pressure_rise(self, res):
        """Calculates the pressure rise due to outgasing.

        .. note::

                An investigation plus measurement is required to find a
                proper way to correct the current outgasing rate measured by IG
                who causes the most of the outgasing.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        outgas_correction = self.get_value('outgas_correction', '1')

        start_time = self.Time.get_value('amt_expansion_start', 'ms')
        end_time = self.Time.get_value('amt_expansion_end', 'ms')
        time_conv = self.Cons.get_conv(from_unit="ms", to_unit="s")
        dt = (end_time - start_time) * time_conv

        pos_dut_a = self.Pos.get_str('dut_a')
        pos_dut_b = self.Pos.get_str('dut_b')
        pos_dut_c = self.Pos.get_str('dut_c')

        outgas_abc = res.pick('OutGasRate', dict_type='outgas_abc', dict_unit='mbar/s', dest='AuxValues')[-1]
        outgas_bc = res.pick('OutGasRate', dict_type='outgas_bc', dict_unit='mbar/s', dest='AuxValues')[-1]
        outgas_c = res.pick('OutGasRate', dict_type='outgas_c', dict_unit='mbar/s', dest='AuxValues')[-1]
        outgas_v = res.pick('OutGasRate', dict_type='outgas_v', dict_unit='mbar/s', dest='AuxValues')[-1]

        # todo: check if cal with outgasing works, max outgasing for now:

        pressure_conv = self.Cons.get_conv(from_unit="mbar", to_unit=self.unit)
        rise =  outgas_v * pressure_conv * dt #* outgas_correction

        res.store('Pressure', 'rise', rise , self.unit)

    def error_pressure_rise(self, res):
        """Calculates the relative contribution of the pressure
        rise due to outgasing.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        p_cal = res.pick('Pressure', 'cal', self.unit)
        p_rise = res.pick('Pressure', 'rise', self.unit)
        e_rise = p_rise/p_cal
        res.store('Error', 'rise', e_rise, '1')

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

        p_rise = res.pick("Pressure", "rise", self.unit)
        self.log.debug("Pressure rise is: {}".format(p_rise))

        T_corr = T_after / T_before
        res.store("Correction", "temperature", T_corr, '1')

        f_prime = 1.0/(1.0 / f + V_add / V_start)
        res.store("Expansion", "corr", f_prime, "1")

        K_real_gas = res.pick("Correction", "rg", "1")
        self.log.debug("real gas correction is: {}".format(K_real_gas))

        K_delta_heigth = res.pick("Correction", "delta_heigth", "1")
        self.log.debug("Heigth correction is: {}".format(K_delta_heigth))

        K_f_pressure =  res.pick("Correction", "f_p_dependency", "1")
        self.log.debug("valve closing pressure dep.: {}".format(K_f_pressure))

        ## calibration pressure:
        p_cal = f_prime * p_fill * K_real_gas * T_corr * K_delta_heigth * K_f_pressure + p_rise
        self.log.debug("calibration pressure in {} is: {}".format(self.unit, p_cal))

        res.store("Pressure", "cal", p_cal, self.unit)

    def pressure_gn_corr(self, res):
        """Calculates the corrected pressures of the group normal (gn)
        """
        meas_time = self.Time.get_value("amt_fill", "ms")

        if res.analysis_type == 'expansion':
            gn_ind_types = self.fill_types
            gn_offset_types = self.offset_types
            gn_target = self.Pres.get_value("target_fill", self.unit)
            sufix = "fill"

        if res.analysis_type == 'direct':
            gn_ind_types = self.compare_types
            gn_offset_types = self.compare_offset_types
            gn_target = self.Pres.get_value("target_pressure", self.unit)
            sufix = "compare"

        for i in range(len(self.FillDevs)):
            GNDevice = self.FillDevs[i]
            if GNDevice.name != self.fill_dev_names[i]:
                sys.exit("Filling pressure devices in unexpected order")

            # get indicated pressure and unit
            p_ind, sd_ind, n_ind, u_ind = self.Pres.get_value_and_unit(gn_ind_types[i], with_stats=True)
            p_ind_conv = p_ind * self.Cons.get_conv(from_unit=u_ind, to_unit=self.unit)

            # get a offset value for each pressure value:
            p_off, u_off = self.Pres.get_value_and_unit(gn_offset_types[i])

            # get one offet value for all pressure values:
            if p_off is None:
                p_off = self.Aux.get_val_by_time(meas_time, "offset_mt", "ms", gn_offset_types[i], self.unit)
                p_off_conv = p_off ## already in self.unit
            else:
                p_off_conv = p_off * self.Cons.get_conv(from_unit=u_off, to_unit=self.unit)

            p = p_ind_conv - p_off_conv

            if sd_ind is not None:
                p[np.where(sd_ind/p_ind > self.gn_sd_threshold)] = np.nan

            if gn_target is not None:
                e = GNDevice.get_error_interpol(p, self.unit, gn_target, self.unit)
            else:
                e = GNDevice.get_error_interpol(p, self.unit, p, self.unit)

            # correct pressure with interpol. values from last calib.
            p_corr = p / (e + 1.0)

            res.store("Pressure", "{dev_name}-{sufix}".format(dev_name=GNDevice.name, sufix=sufix), p_corr, self.unit)
            res.store("Error", "{dev_name}-{sufix}".format(dev_name=GNDevice.name, sufix=sufix), e, '1')
            res.store("Error", "{dev_name}-offset".format(dev_name=GNDevice.name, sufix=sufix), p_off_conv/p_corr, '1')

    def pressure_gn_mean(self, res):
        """
        *) checked that the function `np.ma.average()` gives the same
        result as the function  `self.Pres.weight_array_mean()`
        """
        if res.analysis_type == 'expansion':
            gn_ind_types = self.fill_types
            sufix = "fill"
            res_type ="fill"

        if res.analysis_type == 'direct':
            gn_ind_types = self.compare_types
            sufix = "compare"
            res_type ="cal"

        p_arr = np.array([])
        u_arr = np.array([])
        for i in range(len(self.FillDevs)):
            GNDevice = self.FillDevs[i]
            if GNDevice.name != self.fill_dev_names[i]:
                sys.exit("Filling pressure devicees in unexpected order")

            p_corr = res.pick("Pressure","{dev_name}-{sufix}".format(dev_name=GNDevice.name, sufix=sufix), dict_unit=self.unit)
            e      = res.pick("Error","{dev_name}-{sufix}".format(dev_name=GNDevice.name, sufix=sufix), dict_unit="1")
            e_off  = res.pick("Error","{dev_name}-offset".format(dev_name=GNDevice.name, sufix=sufix), dict_unit="1")
            u_corr = GNDevice.get_total_uncert(p_corr, self.unit, self.unit, take_type_list=["u2", "u3", "u4", "u5", "u6" ])

            ## only use p if u exist
            np.put(p_corr, np.where(np.isnan(u_corr)), np.nan)
            np.put(e, np.where(np.isnan(u_corr)), np.nan)
            np.put(e_off, np.where(np.isnan(u_corr)), np.nan)

            res.store("Pressure", "{dev_name}-{sufix}".format(dev_name=GNDevice.name, sufix=sufix), p_corr, self.unit)
            res.store("Error", "{dev_name}-{sufix}".format(dev_name=GNDevice.name, sufix=sufix), e, '1')
            res.store("Error", "{dev_name}-offset".format(dev_name=GNDevice.name, sufix=sufix), e_off, '1')

            if i == 0:
                p_arr = np.array([p_corr])
                u_arr = np.array([u_corr])
            else:
                p_arr = np.append(p_arr, [p_corr], axis=0)
                u_arr = np.append(u_arr, [u_corr], axis=0)

        p_std = np.nanstd(p_arr, axis=0)
        n = np.apply_along_axis(self.Pres.cnt_nan, axis=0, arr=u_arr)

        w =  np.power(u_arr/p_arr, -1)

        sum_w = np.nansum(w, axis = 0) ## ok
        prod_pw = np.multiply(w, p_arr) ## ok
        p_mean_weight = np.nansum(prod_pw, axis = 0) / sum_w

        #p_mean_weight = np.nanmean(p_arr, axis=0)
        res.store("Pressure", "{res_type}".format(res_type=res_type), p_mean_weight, self.unit, p_std, n)
        res.store("Error", "{res_type}_dev".format(res_type=res_type), p_std/p_mean_weight, "1")

    def correction_delta_height(self, res):
        """Calculates the relative contribution of the pressure
        rise due to outgasing.

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        f_name = self.get_expansion_name()

        p_fill = res.pick("Pressure", "fill", self.unit)


        gas = self.get_gas()

        dp = self.pressure_delta_height(p=p_fill, p_unit=self.unit, f_name=f_name, gas=gas)
        F = 1 + dp/p_fill

        res.store("Correction", "delta_heigth", F,  "1")

    def correction_f_pressure(self, res):
        """Calculates the correction of the expansion
        ratio due to pressure dependency of closing process.
        (see valve paper 6.1 pressure dependend correction factor)

        :param: instance of a class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            pick_dict(quantity, type)
        :type: class
        """
        f_name = self.get_expansion_name()
        F  = np.full(len(f_name), 1.0)

        ## hard wired unit because of corr_f_p_a
        p_fill = res.pick("Pressure", "fill", "Pa")

        i_s = np.where(f_name == "f_s")
        if np.shape(i_s)[1] > 0:
            a = self.get_value("corr_f_p_a", "1/Pa")
            b = self.get_value("corr_f_p_b", "1")

            F[i_s] = (1 - a * p_fill[i_s] + b)

        res.store("Correction", "f_p_dependency", F,  "1")

    def pressure_delta_height(self, p, p_unit, f_name, gas="N2"):
        """ Follows QSE-SE3-19-3 at http://a73435.berlin.ptb.de:82/lab?
        """

        n = len(p)
        dp = np.full(n, np.nan)
        h_i = np.full(n, np.nan)

        i_s = np.where(f_name == "f_s")
        i_m = np.where(f_name == "f_m")
        i_l = np.where(f_name == "f_l")

        if np.shape(i_s)[1] > 0:
            h_i[i_s] = self.get_value("h_s", "m")

        if np.shape(i_m)[1] > 0:
            h_i[i_m] = self.get_value("h_m", "m")

        if np.shape(i_l)[1] > 0:
            h_i[i_l] = self.get_value("h_l", "m")

        p = p * self.Cons.get_conv(from_unit=p_unit, to_unit="Pa")

        M = self.Cons.get_value("molWeight_{gas}".format(gas=gas), "kg/mol")
        R = self.Cons.get_value("R","Pa m^3/mol/K" )
        T = self.Cons.get_value("referenceTemperature", "K")
        g = self.Cons.get_value("g", "m/s^2")

        dp = - h_i * p * M * g /R / T

        return dp * self.Cons.get_conv(from_unit="Pa", to_unit=self.unit)

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
                store(quantity, type, value, unit, [stdev], [N]) and
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
        t_mean, t_stdv, t_N = self.temperature(list(range(2029, 2031)), "_after")
        res.store("Temperature", "room", t_mean, "K", t_stdv, t_N)

    def temperature_comp(self, res):
        """Calculates the temperature of the room.

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N]) and
                pick(quantity, type, unit)
        :type: class
        """
        t_mean, t_stdv, t_N = self.temperature(list(range(2029, 2031)), "_room")
        res.store("Temperature", "compare", t_mean, "K", t_stdv, t_N)
        # same same
        res.store("Temperature", "room", t_mean, "K", t_stdv, t_N)

    def temperature_gas_expansion(self, res):
        """Defines the gas temperature as the vessel
         temperature after expansion

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N]) and
                pick(quantity, type, unit)
        :type: class
        """
        gas_temp = res.pick('Temperature', 'after', 'K')
        res.store("Temperature", "gas", gas_temp, "K")

    def temperature_gas_direct(self, res):
        """Defines the gas temperature as the
         temperature of the vacuum pipes

        :param: instance of a class with methode
                store(quantity, type, value, unit, [stdev], [N]) and
                pick(quantity, type, unit)
        :type: class
        """
        gas_temp = res.pick('Temperature', 'compare', 'K')
        res.store("Temperature", "gas",gas_temp , "K")


    def offset_from_sample(self, res):
        range_offset_trans = {
           "X1":"offset_x1",
           "X0.1":"offset_x0.1",
           "X0.01":"offset_x0.01"
        }

        range_str_arr = self.Range.get_str("ind")
        if range_str_arr is not None:
            offs = np.full(self.no_of_meas_points, np.nan)
            sd_offs = np.full(self.no_of_meas_points, np.nan)
            n_offs = np.full(self.no_of_meas_points, np.nan)
            range_unique = np.unique(range_str_arr)
            for r in range_unique:
                i_r = np.where(range_str_arr == r)
                if np.shape(i_r)[1] > 0:
                    offset_sample_value, sample_unit = self.Aux.get_value_and_unit(type=range_offset_trans[r])
                    offs[i_r] = np.nanmean(offset_sample_value)
                    n_offs[i_r] = np.count_nonzero(~np.isnan(offset_sample_value))
                    sd_offs[i_r]= np.nanstd(offset_sample_value)

        else:
            offset_sample_value, sample_unit = self.Aux.get_value_and_unit(type="offset")
            offs = np.full(self.no_of_meas_points, np.nanmean(offset_sample_value))
            sd_offs = np.full(self.no_of_meas_points, np.nanstd(offset_sample_value))
            n_offs = np.full(self.no_of_meas_points, np.count_nonzero(~np.isnan(offset_sample_value)))

        res.store("Pressure", "offset_sample", offs , sample_unit, sd_offs , n_offs)

    def all(self, ana):
        self.pressure_gn_corr(ana)
        self.pressure_gn_mean(ana)
        self.deviation_target_fill(ana)
        self.temperature_before(ana)
        self.temperature_after(ana)
        self.temperature_room(ana)
        self.temperature_gas_expansion(ana)
        self.real_gas_correction(ana)
        self.volume_add(ana)
        self.volume_start(ana)
        self.expansion(ana)
        self.pressure_rise(ana)
        self.correction_delta_height(ana)
        self.correction_f_pressure(ana)
        self.pressure_cal(ana)
        self.error_pressure_rise(ana)
        self.deviation_target_cal(ana)
