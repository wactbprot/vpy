import sys
import numpy as np
import sympy as sym
from .std import Se3


class Uncert(Se3):

    def __init__(self, doc):
        super().__init__(doc)

    def define_model(self):
        """ Defines symbols and model for the static expansion system SE3.
        The order of symbols must match the order in ``gen_val_arr``:

        # . f
        # . p_fill
        # . V_5
        # . V_start
        # . p_before
        # . p_after

        The equation is:

        .. math::

                p = f_{corr} p_{fill}

        with

        .. math::

                f_{corr} = \\frac{1}{ \\frac{1}{f} + \\frac{V_{add}}{V_{start}}}


        :type: class
        """
        self.model_unit="mbar"

        f=sym.Symbol('f')
        p_fill=sym.Symbol('p_fill')
        V_start=sym.Symbol('V_start')
        V_add=sym.Symbol('V_add')
        T_before=sym.Symbol('T_before')
        T_after=sym.Symbol('T_after')
        rg=sym.Symbol('rg')

        self.symb=(
                    f,
                    p_fill,
                    V_start,
                    V_add,
                    T_before,
                    T_after,
                    rg,
                    )

        self.model=p_fill * 1.0 / (1.0 / f + V_add / V_start) / T_before * T_after / rg

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as define_models symbols order:

        # . f
        # . p_fill
        # . V_5
        # . V_start
        # . V_add
        # . T_before
        # . T_after

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        self.val_arr=[
                    self.val_dict['f'],
                    self.val_dict['p_fill'],
                    self.val_dict['V_start'],
                    self.val_dict['V_add'],
                    self.val_dict['T_before'],
                    self.val_dict['T_after'],
                    self.val_dict['rg'],
                    ]

    def gen_val_dict(self, res):
        """Reads in a dict of values
        with the same order as in ``define_models``. For the calculation
        of the gas density, the Frs reading is multiplied by 10 which gives a
        sufficient approximation for the pressure.

        :param: Class with method
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        self.val_dict={
        'f': res.pick("Expansion", "uncorr", "1"),
        'p_fill': res.pick("Pressure", "fill", self.unit),
        'T_before': res.pick("Temperature", "before", "K"),
        'T_after': res.pick("Temperature", "after", "K"),
        'rg': res.pick("Correction", "rg", "1"),
        }
        vol_start = res.pick("Volume", "start", "cm^3")
        vol_add =res.pick("Volume", "start", "cm^3")
        
        if vol_add is None:
            vol_add = 0.0
            vol_start = 1.0

        self.val_dict['V_start'] = vol_start
        self.val_dict['V_add'] = vol_add

    def total_standard(self, res):
        u_1 = res.pick("Uncertainty", "v_start", "1")
        u_2 = res.pick("Uncertainty", "v_5", "1")
        u_3 = res.pick("Uncertainty", "p_fill", "1")
        u_4 = res.pick("Uncertainty", "t_before", "1")
        u_5 = res.pick("Uncertainty", "t_after", "1")
        u_6 = res.pick("Uncertainty", "f", "1")
        
        u_t = np.sqrt(np.power(u_1, 2) +
                      np.power(u_2, 2) +
                      np.power(u_3, 2) +
                      np.power(u_4, 2) +
                      np.power(u_5, 2) +
                      np.power(u_6, 2)
                      )
        res.store("Uncertainty", "standard", u_t, "1")
        
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
        val = np.abs(u(*self.val_arr) * u_pro * 2)

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
        val = np.abs(u(*self.val_arr) * u_pro)

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

        fill_res = res.pick("Pressure", "fill", self.unit)

        N = len(self.fill_dev_names)
        M = self.no_of_meas_points
        u_arr = []

        for i in range(N):
            Dev = self.FillDevs[i]
            u_i = Dev.get_total_uncert(fill_res, self.unit, self.unit, res=res)
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
   
    def expansion(self, res):
        """Calculates the uncertainty contribution
        of the axpansion factor

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f_name = self.get_expansion_name()
        f = np.full(self.no_of_meas_points, np.nan)

        i_l = np.where(f_name == "f_l")
        i_m = np.where(f_name == "f_m")
        i_s = np.where(f_name == "f_s")

        if np.shape(i_s)[1] > 0:
            f[i_s] = self.get_value("u_f_s", "1") * self.get_value("f_s", "1")

        if np.shape(i_m)[1] > 0:
            f[i_m] = self.get_value("u_f_m", "1")* self.get_value("f_m", "1")

        if np.shape(i_l)[1] > 0:
            f[i_l] = self.get_value("u_f_l", "1") * self.get_value("f_l", "1")

        s_expr = sym.diff(self.model, sym.Symbol('f'))
        u = sym.lambdify(self.symb, s_expr, "numpy")
        val = u(*self.val_arr) * f

        p_nom = self.val_dict['f'] * self.val_dict['p_fill']

        res.store("Uncertainty", "f", np.absolute(val / p_nom), "1")
        self.log.debug("uncert f: {}".format(val / p_nom))

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

    
    def cmc(self, ana):
        p_list = ana.pick("Pressure", "cal", "Pa")
        
        u = np.asarray([np.piecewise(p, [p <= 0.027, (p > 0.027 and p <= 0.3), (p > 0.3 and p <= 0.73), (p >0.73 and p <= 9.), (p > 9. and p <= 1000.), (p > 1000. and p <= 8000.),  8000. < p]
                                       ,[0.0014,                        0.001,                 0.00092,              0.00086,                 0.00075,                   0.00019,  0.00014] ).tolist() for p in p_list])

        ana.store("Uncertainty", "standard", u , "1")

