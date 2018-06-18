import numpy as np
import sympy as sym

from .std import Se3


class Uncert(Se3):

    def __init__(self, doc):
        super().__init__(doc)

    def total(self, res):

        self.gen_val_dict(res)
        self.gen_val_array(res)

        self.volume_start(res)
        self.volume_5(res)
        self.pressure_fill(res)
        self.temperature_before(res)
        self.temperature_after(res)

        u_1 = res.pick("Uncertainty", "v_start", "1")
        u_2 = res.pick("Uncertainty", "v_5", "1")
        u_3 = res.pick("Uncertainty", "p_fill", "1")
        u_4 = res.pick("Uncertainty", "t_before", "1")
        u_5 = res.pick("Uncertainty", "t_after", "1")

        u_t = np.sqrt(np.power(u_1, 2) +
                      np.power(u_2, 2) +
                      np.power(u_3, 2) +
                      np.power(u_4, 2) +
                      np.power(u_5, 2)
                      )

        res.store("Uncertainty", "total", u_t, "1")
        self.log.info("Calibration pressure: {}".format(
            self.val_dict["f"] * self.val_dict["p_fill"]))
        self.log.info("Uncertainty total: {}".format(u_t))

    def temperature_after(self, res):
        """ Calculates the uncertainty of the temperature after expasion.

        .. attention::
            The Uncertainty is multiplied by 2 in order to
            have an upper estimation of that value

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        N_arr = np.full(self.no_of_meas_points, len(self.vessel_temp_types))

        u = self.TDev.get_total_uncert(self.val_dict["T_after"], "K", "K")

        u_pro = u / np.sqrt(N_arr)

        s_expr = sym.diff(self.model, sym.Symbol("T_after"))
        u = sym.lambdify(self.symb, s_expr, "numpy")
        # Sicherheitsfaktor
        val = u(*self.val_arr) * u_pro * 2

        p_nom = self.val_dict["f"] * self.val_dict["p_fill"]

        res.store("Uncertainty", "t_after", val / p_nom, "1")
        self.log.debug("uncert u_t_after: {}".format(val / p_nom))

    def temperature_before(self, res):
        """ Calculates the uncertainty of the temperature before expasion.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        f = self.get_expansion_name()
        i_l = np.where(f == "f_l")
        i_m = np.where(f == "f_m")
        i_s = np.where(f == "f_s")

        N_arr = np.full(self.no_of_meas_points, np.nan)

        if np.shape(i_s)[1] > 0:
            N_arr[i_s] = len(self.small_temp_types)

        if np.shape(i_m)[1] > 0:
            N_arr[i_m] = len(self.medium_temp_types)

        if np.shape(i_l)[1] > 0:
            N_arr[i_l] = len(self.large_temp_types)

        u = self.TDev.get_total_uncert(self.val_dict["T_before"], "K", "K")

        u_pro = u / np.sqrt(N_arr)

        s_expr = sym.diff(self.model, sym.Symbol("T_before"))
        u = sym.lambdify(self.symb, s_expr, "numpy")
        val = u(*self.val_arr) * u_pro

        p_nom = self.val_dict["f"] * self.val_dict["p_fill"]

        res.store("Uncertainty", "t_before", val / p_nom, "1")
        self.log.debug("uncert u_t_before: {}".format(val / p_nom))

    def pressure_fill(self, res):
        """ Calculates the uncertainty of the filling pressure_fill.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        fill_target = self.Pres.get_value("target-fill", "mbar")

        N = len(self.fill_dev_names)
        M = self.no_of_meas_points
        u_arr = []

        for i in range(N):
            Dev = self.FillDevs[i]
            u_i = Dev.get_total_uncert(fill_target, "mbar", self.unit)
            u_arr.append(u_i)

        u_comb = np.power(np.nansum(np.power(u_arr, -1), axis=0), -1)

        s_expr = sym.diff(self.model, sym.Symbol("p_fill"))
        u = sym.lambdify(self.symb, s_expr, "numpy")
        val = u(*self.val_arr) * u_comb

        p_nom = self.val_dict["f"] * self.val_dict["p_fill"]

        res.store("Uncertainty", "p_fill", val / p_nom, "1")
        self.log.debug("uncert u_p_fill: {}".format(val / p_nom))

    def volume_start(self, res):
        """Calculates the uncertainty contribution
        of the starting volume

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f = self.get_expansion_name()
        V = np.full(self.no_of_meas_points, np.nan)

        i_l = np.where(f == "f_l")
        i_m = np.where(f == "f_m")
        i_s = np.where(f == "f_s")

        if np.shape(i_s)[1] > 0:
            V[i_s] = self.get_value("u_V_s", "cm^3")

        if np.shape(i_m)[1] > 0:
            V[i_m] = self.get_value("u_V_m", "cm^3")

        if np.shape(i_l)[1] > 0:
            V[i_l] = self.get_value("u_V_l", "cm^3")

        s_expr = sym.diff(self.model, sym.Symbol('V_start'))
        u = sym.lambdify(self.symb, s_expr, "numpy")
        val = u(*self.val_arr) * V

        p_nom = self.val_dict['f'] * self.val_dict['p_fill']

        res.store("Uncertainty", "v_start", np.absolute(val / p_nom), "1")
        self.log.debug("uncert v_start: {}".format(val / p_nom))

    def volume_5(self, res):
        """Calculates the uncertainty contribution
         of the  volume 5

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            :type: class
            """

        u_V_5 = np.full(self.no_of_meas_points,
                        self.get_value("u_V_5", "cm^3"))
        s_expr = sym.diff(self.model, sym.Symbol('V_5'))
        u = sym.lambdify(self.symb, s_expr, "numpy")
        val = u(*self.val_arr) * u_V_5

        p_nom = self.val_dict['f'] * self.val_dict['p_fill']

        res.store("Uncertainty", "v_5", np.absolute(val / p_nom), "1")
        self.log.debug("uncert v_5: {}".format(val / p_nom))
