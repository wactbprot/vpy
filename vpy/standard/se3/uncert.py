import sys
import numpy as np
from .std import Se3

class Uncert(Se3):

    volume_unit = "cm^3"
    pressure_unit = "Pa"
    temperature_unit = "K"
    rel_unit = "1"

    def __init__(self, doc):
        super().__init__(doc)

    # -------------------------
    ## add volume
    # -------------------------
    def volume_add_sens_volume_5(self, V_5, p_0, p_1, p_r):
        return (p_1 - p_r)/(p_0 - p_1)

    def volume_add_sens_pressure_0(self, V_5, p_0, p_1, p_r):
        return -V_5*(p_1 - p_r)/(p_0 - p_1)**2

    def volume_add_sens_pressure_1(self, V_5, p_0, p_1, p_r):
        return V_5/(p_0 - p_1) + V_5*(p_1 - p_r)/(p_0 - p_1)**2

    def volume_add_sens_pressure_r(self, V_5, p_0, p_1, p_r):
        return -V_5/(p_0 - p_1)

    def volume_add_volume_5(self, u_V_5, V_5_unit, V_5, p_0, p_1, p_r):
        if V_5_unit == "1":
            u = u_V_5 * V_5
        elif V_5_unit == self.volume_unit:
            u = u_V_5
        else:
            msg = "wrong unit in uncert_volume_5"
            self.log.error(msg)
            sys.exit(msg)

        return self.volume_add_sens_volume_5(V_5, p_0, p_1, p_r) * u

    def volume_add_pressure_0(self, u_p_0, p_0_unit, V_5, p_0, p_1, p_r):
        if p_0_unit == self.rel_unit:
            u = u_p_0 * p_0
        elif p_0_unit == self.pressure_unit:
            u = u_p_0
        else:
            msg = "wrong unit in uncert_pressure_0"
            self.log.error(msg)
            sys.exit(msg)

        return self.volume_add_sens_pressure_0(V_5, p_0, p_1, p_r) * u

    def volume_add_pressure_1(self, u_p_1, p_1_unit, V_5, p_0, p_1, p_r):
        if p_1_unit == self.rel_unit:
            u = u_p_1 * p_1
        elif p_1_unit == self.pressure_unit:
            u = u_p_1
        else:
            msg = "wrong unit in uncert_pressure_1"
            self.log.error(msg)
            sys.exit(msg)

        return self.volume_add_sens_pressure_1(V_5, p_0, p_1, p_r) * u

    def volume_add_pressure_r(self, u_p_r, p_r_unit, V_5, p_0, p_1, p_r):
        if p_r_unit == self.rel_unit:
            u = u_p_r * p_r
        elif p_r_unit == self.pressure_unit:
            u = u_p_r
        else:
            msg = "wrong unit in uncert_pressure_r"
            self.log.error(msg)
            sys.exit(msg)

        return self.volume_add_sens_pressure_r(V_5, p_0, p_1, p_r) * u

    # -------------------------
    ## calib. pressure
    # -------------------------
    def sens_pressure_fill(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return F*T_after/T_before/(V_add/V_start + 1/f)

    def sens_pressure_rise(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return np.array([1])

    def sens_expansion(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return F*T_after*p_fill/(T_before*f**2*(V_add/V_start + 1/f)**2)

    def sens_volume_add(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return -F*T_after*p_fill/(T_before*V_start*(V_add/V_start + 1/f)**2)

    def sens_volume_start(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return F*T_after*V_add*p_fill/(T_before*V_start**2*(V_add/V_start + 1/f)**2)

    def sens_temperature_after(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return F/T_before*p_fill/(V_add/V_start + 1./f)

    def sens_temperature_before(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return -F*T_after*p_fill/(T_before**2*(V_add/V_start + 1/f))

    def sens_corr_factors(self, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        return 	T_after/T_before*p_fill/(V_add/V_start + 1/f)

    def group_normal_n_vec(self, u_array):
        return  np.apply_along_axis(self.Vals.cnt_nan, axis=0, arr=u_array)

    def group_normal_array(self, p, unit, take_type_list=None, skip_type=None):
        N = len(self.fill_dev_names)
        u_arr = []

        for i in range(N):
            Dev = self.FillDevs[i]
            u_i = Dev.get_total_uncert(p, unit, self.pressure_unit, take_type_list=take_type_list, skip_type=skip_type)
            u_arr.append(u_i)

        return u_arr

    def contrib_temperature_vessel(self, T, T_unit, skip_type=None):
        """Calculation of uncertainty follows QSE-SE3-19-1.ipynb
        (http://a73435.berlin.ptb.de:82/lab)


        The contributions u_T_ch_cal u_T_ch (here u) appear N times so that:  sqrt 1/N^2 * N * u
        """
        N = len(self.vessel_temp_types)

        u_T_ptb = self.TDev.get_total_uncert(T, T_unit, self.temperature_unit, take_type_list=["u1"], skip_type=skip_type)
        u_T_ch_cal = self.TDev.get_total_uncert(T, T_unit, self.temperature_unit, take_type_list=["u2", "u3", "u6"], skip_type=skip_type)
        u_T_ch = self.TDev.get_total_uncert(T, T_unit, self.temperature_unit, take_type_list=["u3" ,"u4", "u5", "u6"], skip_type=skip_type)

        ## sqrt 1/N^2 * N * u
        u_total = np.sqrt(np.power(u_T_ptb, 2) +  1/N*np.power(u_T_ch_cal, 2) + 1/N*np.power(u_T_ch, 2))

        return u_total

    def contrib_temperature_after(self, T, T_unit, skip_type=None):
        """Calculation of uncertainty follows QSE-SE3-19-1.ipynb
        (http://a73435.berlin.ptb.de:82/lab)

        """
        u_1 = self.contrib_temperature_vessel(T, T_unit)
        u_2 = self.get_value("u_T_after_2", self.temperature_unit)
        u_3 = self.get_value("u_T_after_3", self.temperature_unit)
        u_4 = self.get_value("u_T_after_4", self.temperature_unit)
        u_5 = self.get_value("u_T_after_5", self.temperature_unit)

        return  np.sqrt(np.power(u_1, 2) + np.power(u_2, 2) +np.power(u_3, 2) +np.power(u_4, 2) +np.power(u_5, 2))

    def contrib_temperature_volume_start(self, T, T_unit, f_name, skip_type=None):
        """Calculation of uncertainty follows QSE-SE3-19-1.ipynb
        (http://a73435.berlin.ptb.de:82/lab)

        """
        N = np.full(len(T), np.nan)

        i_s = np.where(f_name == "f_s")
        i_m = np.where(f_name == "f_m")
        i_l = np.where(f_name == "f_l")

        if len(i_s) > 0:
            N[i_s] = len(self.small_temp_types)
        if len(i_m) > 0:
            N[i_m] = len(self.medium_temp_types)
        if len(i_l) > 0:
            N[i_l] = len(self.large_temp_types)

        u_T_ptb = self.TDev.get_total_uncert(T, T_unit, self.temperature_unit, take_type_list=["u1"], skip_type=skip_type)
        u_T_ch_cal = self.TDev.get_total_uncert(T, T_unit, self.temperature_unit, take_type_list=["u2", "u3", "u6"], skip_type=skip_type)
        u_T_ch =  self.TDev.get_total_uncert(T, T_unit, self.temperature_unit, take_type_list=["u3" ,"u4", "u5", "u6"], skip_type=skip_type)

        ## sqrt 1/N^2 * N * u
        u_total = np.sqrt(np.power(u_T_ptb, 2) +  np.divide(np.power(u_T_ch_cal, 2), N) + np.divide(np.power(u_T_ch, 2),N))

        return u_total

    def contrib_temperature_before(self, T, T_unit, f_name, skip_type=None):
        """Calculation of uncertainty follows QSE-SE3-19-1.ipynb
        (http://a73435.berlin.ptb.de:82/lab)

        """
        i_s = np.where(f_name == "f_s")
        i_m = np.where(f_name == "f_m")
        i_l = np.where(f_name == "f_l")

        u_1 = self.contrib_temperature_volume_start(T, T_unit, f_name)
        u_2 = self.get_value("u_T_before_2", self.temperature_unit)
        u_3 = np.full(len(T), np.nan)
        if len(i_s) > 0:
            u_3[i_s] = self.get_value("u_T_before_s_3", self.temperature_unit)
        if len(i_m) > 0:
            u_3[i_m] = self.get_value("u_T_before_m_3", self.temperature_unit)
        if len(i_l) > 0:
            u_3[i_l] = self.get_value("u_T_before_l_3", self.temperature_unit)

        u_4 = self.get_value("u_T_before_4", self.temperature_unit)
        u_5 = self.get_value("u_T_before_5", self.temperature_unit)

        return  np.sqrt(np.power(u_1, 2) + np.power(u_2, 2) +np.power(u_3, 2) +np.power(u_4, 2) +np.power(u_5, 2))


    def contrib_pressure_fill(self, p_fill, p_fill_unit, skip_type=None):
        """Calculation of uncertainty follows QSE-SE3-19-1.ipynb
        (http://a73435.berlin.ptb.de:82/lab)
        """
        u_p_cal_abs = self.group_normal_array(p_fill, p_fill_unit, take_type_list=["u1"], skip_type=skip_type)
        u_p_fill_abs = self.group_normal_array(p_fill, p_fill_unit, take_type_list=["u2", "u3", "u4", "u5", "u6" ], skip_type=skip_type)
        u_p_ind_abs = self.group_normal_array(p_fill, p_fill_unit, take_type_list=["u2", "u4", "u5", "u6" ], skip_type=skip_type)

        ## no need to skip_types for weights
        w =  np.power(self.group_normal_array(p_fill, p_fill_unit, take_type_list=["u1", "u2", "u3", "u4", "u5", "u6" ]), -1)
        sum_w = np.nansum(w, axis = 0)

        u_p_cal_abs = self.Vals.square_array_sum(u_p_cal_abs)
        u_p_ind_abs = self.Vals.square_array_sum(np.divide(np.multiply(w, u_p_ind_abs), sum_w))
        u_p_fill_abs = self.Vals.square_array_sum(np.divide(np.multiply(w, u_p_fill_abs), sum_w))

        u_total_w = np.sqrt(np.power(u_p_cal_abs, 2) +  np.power(u_p_ind_abs, 2) + np.power(u_p_fill_abs, 2))

        return u_total_w

    def contrib_pressure_rise(self, p_rise, p_rise_unit, skip_type=None):
        u = self.get_value("u_outgas_correction", self.rel_unit)
        return u * p_rise

    #def contrib_corr_factors(self, u_p_fill, p_fill_unit, skip_type=None):
        #u_1 = np.abs(self.get_value("u_gas_dependency_1", self.rel_unit) *(1 -  ...

    def pressure_fill(self, u_p_fill, p_fill_unit, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        if p_fill_unit == self.rel_unit:
            u = u_p_fill * p_fill
        elif p_fill_unit == self.pressure_unit:
            u = u_p_fill
        else:
            msg = "wrong unit in uncert.pressure_fill"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_pressure_fill(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u

    def pressure_rise(self, u_p_rise, p_rise_unit,  p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        if p_rise_unit == self.rel_unit:
            u = u_p_rise * p_rise
        elif p_rise_unit == self.pressure_unit:
            u = u_p_rise
        else:
            msg = "wrong unit in uncert.pressure_rise"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_pressure_rise(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u

    def expansion(self, u_f_abs, f_unit, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        """
        .. note::

                unit for abs. and rel. uncert. both = 1 (!)
        """
        return self.sens_expansion(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u_f_abs

    def volume_add(self, u_V_add, V_add_unit, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        if V_add_unit == self.rel_unit:
            u = u_V_add * V_add
        elif V_add_unit == self.volume_unit:
            u = u_V_add
        else:
            msg = "wrong unit in uncert.volume_add"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_volume_add(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u

    def volume_start(self, u_V_start, V_start_unit, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        if V_start_unit == self.rel_unit:
            u = u_V_start * V_start
        elif V_start_unit == self.volume_unit:
            u = u_V_start
        else:
            msg = "wrong unit in uncert.volume_start"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_volume_start(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u


    def temperature_after(self, u_T_after, T_after_unit, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        if T_after_unit == self.rel_unit:
            u = u_T_after * T_after
        elif T_after_unit == self.temperature_unit:
            u = u_T_after
        else:
            msg = "wrong unit in uncert.temperature_after"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_temperature_after(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u

    def temperature_before(self, u_T_before, T_before_unit, p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        if T_before_unit == self.rel_unit:
            u = u_T_before * T_before
        elif T_before_unit == self.temperature_unit:
            u = u_T_before
        else:
            msg = "wrong unit in uncert.temperature_after"
            self.log.error(msg)
            sys.exit(msg)

        return self.sens_temperature_before(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u

    def corr_factors(self, u_F_abs, F_unit,  p_fill, p_rise, f, V_add, V_start, T_after, T_before, F):
        """
        .. note::

                unit for abs. and rel. uncert. both = 1 (!)
        """
        return self.sens_corr_factors(p_fill, p_rise, f, V_add, V_start, T_after, T_before, F) * u_F_abs

    # -------------------------
    ## vaclab cmc records
    # -------------------------
    def cmc(self, ana):
        p_list = ana.pick("Pressure", "cal", self.pressure_unit)

        u = np.asarray([np.piecewise(p, [p <= 0.027, (p > 0.027 and p <= 0.3), (p > 0.3 and p <= 0.73), (p >0.73 and p <= 9.), (p > 9. and p <= 1000.), (p > 1000. and p <= 8000.),  8000. < p]
                                       ,[0.0014,                        0.001,                 0.00092,              0.00086,                 0.00075,                   0.00019,  0.00014] ).tolist() for p in p_list])

        ana.store("Uncertainty", "standard", u , "1")
