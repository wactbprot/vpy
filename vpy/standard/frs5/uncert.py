import numpy as np
import sympy as sym

from .std import Frs5

class Uncert(Frs5):

    def __init__(self, doc):
        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def define_model(self):
        """ Defines symbols and model for FRS5.
        The order of symbols must match the order in ``gen_val_arr``:

        #. A
        #. r
        #. r_zc
        #. r_zc0
        #. r_cal
        #. r_cal0
        #. ub
        #. usys
        #. p_res
        #. m_cal
        #. g
        #. T
        #. rho_frs
        #. rho_gas
        #. ab

        The equation is:

        .. math::

                p=\\frac{r}{r_{cal}} m_{cal}\\frac{g}{A_{eff}}\\
                \\frac{1}{corr_{rho}corr_{tem}} + p_{res}

        with

        .. math::

                corr_{rho} = 1 - \\frac{\\rho_{gas}}{\\rho_{piston}}

        and

        .. math::

                corr_{tem} = 1 + \\alpha \\beta (\\vartheta - 20)


        :type: class
        """
        A = sym.Symbol('A')
        r = sym.Symbol('r')
        r_zc = sym.Symbol('r_zc')
        r_zc0 = sym.Symbol('r_zc0')
        r_cal = sym.Symbol('r_cal')
        r_cal0 = sym.Symbol('r_cal0')
        ub = sym.Symbol('ub')
        usys = sym.Symbol('usys')
        m_cal = sym.Symbol('m_cal')
        g = sym.Symbol('g')
        rho_frs = sym.Symbol('rho_frs')
        rho_gas = sym.Symbol('rho_gas')
        ab = sym.Symbol('ab')
        T = sym.Symbol('T')
        p_res = sym.Symbol('p_res')

        self.symb = (
            A,
            r,
            r_zc,
            r_zc0,
            r_cal,
            r_cal0,
            ub,
            usys,
            m_cal,
            g,
            rho_frs,
            rho_gas,
            ab,
            T,
            p_res,)

        self.model_offset = r_zc - r_zc0
        self.model_buoyancy = 1.0 / (1.0 - rho_gas / rho_frs)
        self.model_temp = 1.0 / (1.0 + ab * (T - 20.0))
        self.model_conv = m_cal / (r_cal - r_cal0) * \
            g / A * self.model_buoyancy * self.model_temp
        # all together
        self.model = (r - self.model_offset + ub + usys) * \
            self.model_conv + p_res

    def gen_val_dict(self, res):
        """Reads in a dict of values
        with the same order as in ``define_models``. For the calculation
        of the gas density, the Frs reading is multiplyed by 10 which gives a
        suffucient approximation for the pressure.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        self.model_unit = "Pa"
        N = self.no_of_meas_points

        gas = self.get_gas()

        conv_p = self.Cons.get_conv(self.unit, self.model_unit)
        conv_T = self.Cons.get_conv("C", "K")

        T = res.pick("Temperature", "frs5", "C")

        meas_time = self.Time.get_value("amt_meas", "ms")

        # correction buoyancy  get info for gas
        approx_p = self.Pres.get_value("frs_p", "lb") * 10.0  # mbar

        val_rho_gas = self.Cons.get_gas_density(gas, approx_p, self.unit,
                                                T + conv_T, "K", "kg/m^3")

        self.val_dict = {
            'A':       self.get_value_full("A_eff", "m^2", N),
            'r':       self.Pres.get_value("frs_p", "lb"),
            'r_zc':    self.Pres.get_value("frs_zc_p", "lb"),
            'r_zc0':   self.Aux.get_val_by_time(meas_time, "amt_offset", "ms", "frs_zc0_p", "lb"),
            'r_cal':   self.get_value_full("R_cal", "lb", N),
            'r_cal0':  np.full(self.no_of_meas_points, 0.0),
            'ub':      np.full(self.no_of_meas_points, 0.0),
            'usys':    np.full(self.no_of_meas_points, 0.0),
            'm_cal':   self.get_value_full("m_cal", "kg", N),
            'g':       self.get_value_full("g_frs", "m/s^2", N),
            'rho_frs': self.get_value_full("rho_frs", "kg/m^3", N),
            'rho_gas': val_rho_gas,
            'ab':      self.get_value_full("alpha_beta_frs", "1/C", N),
            'T':       T,
            'p_res':   res.pick("Pressure", "frs5_res", self.unit) * conv_p,
        }

        self.log.info("value dict genetated")
        self.log.debug(self.val_dict)

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as define_models symbols order:

        #. A
        #. r
        #. r_zc
        #. r_zc0
        #. r_cal
        #. r_cal0
        #. ub
        #. usys
        #. m_cal
        #. g
        #. rho_frs
        #. rho_gas
        #. ab
        #. T
        #. p_res

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        self.gen_val_dict(res)
        self.val_arr = [
            self.val_dict['A'],
            self.val_dict['r'],
            self.val_dict['r_zc'],
            self.val_dict['r_zc0'],
            self.val_dict['r_cal'],
            self.val_dict['r_cal0'],
            self.val_dict['ub'],
            self.val_dict['usys'],
            self.val_dict['m_cal'],
            self.val_dict['g'],
            self.val_dict['rho_frs'],
            self.val_dict['rho_gas'],
            self.val_dict['ab'],
            self.val_dict['T'],
            self.val_dict['p_res'],
        ]
        self.log.info("value array derived from dict_arr")
        self.log.debug(self.val_arr)

    def total_standard(self, res):
        """Calculates the total uncertainty.
        sympy derives the sensitivity coefficients.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        self.define_model()
        self.gen_val_array(res)

        self.uncert_r(res)
        self.uncert_r_zc(res)
        self.uncert_r_zc0(res)
        self.uncert_ub(res)
        self.uncert_usys(res)
        self.uncert_m_cal(res)
        self.uncert_g(res)
        self.uncert_A(res)
        self.uncert_T(res)
        self.uncert_rho_gas(res)
        self.uncert_rho_frs(res)
        self.uncert_r_cal(res)
        self.uncert_r_cal0(res)
        self.uncert_ab(res)

        u_total = (
                    res.pick("Uncertainty", "u_ab", "1")**2
                    + res.pick("Uncertainty", "u_r", "1")**2
                    + res.pick("Uncertainty", "u_r_zc", "1")**2
                    + res.pick("Uncertainty", "u_r_zc0", "1")**2
                    + res.pick("Uncertainty", "u_ub", "1")**2
                    + res.pick("Uncertainty", "u_usys", "1")**2
                    + res.pick("Uncertainty", "u_m_cal", "1")**2
                    + res.pick("Uncertainty", "u_r_cal", "1")**2
                    + res.pick("Uncertainty", "u_r_cal0", "1")**2
                    + res.pick("Uncertainty", "u_g", "1")**2
                    + res.pick("Uncertainty", "u_A", "1")**2
                    + res.pick("Uncertainty", "u_T", "1")**2
                    + res.pick("Uncertainty", "u_rho_gas", "1")**2
                    + res.pick("Uncertainty", "u_rho_frs", "1")**2
                    )**0.5

        p = res.pick("Pressure", "cal", self.unit)
        res.store("Uncertainty", "frs5_total_rel", u_total, "1")
        res.store("Uncertainty", "frs5_total_abs", u_total*p, self.unit)
        self.log.debug("uncert total: {}".format(u_total))


    def uncert_r(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r'))
        u_expr = self.get_expression("u_r", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        res.store("Uncertainty", "u_r", np.absolute(val/p), "1")
        self.log.debug("uncert r: {}".format(val/p))

    def uncert_r_zc(self, res):
        """Calculates the uncertainty of the r_zc
        (zero check between measurement points)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r_zc'))
        u_expr = self.get_expression("u_r_zc", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert r_zc: {}".format(val/p))
        res.store("Uncertainty", "u_r_zc", np.absolute(val/p), "1")

    def uncert_r_zc0(self, res):
        """Calculates the uncertainty of the r_zc0 (initial zero check)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r_zc0'))
        u_expr = self.get_expression("u_r_zc0", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert r_zc0: {}".format(val/p))
        res.store("Uncertainty", "u_r_zc0", np.absolute(val/p), "1")

    def uncert_ub(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('ub'))
        u_expr = self.get_expression("u_ub", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert ub: {}".format(val/p))
        res.store("Uncertainty", "u_ub", np.absolute(val/p), "1")

    def uncert_usys(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('usys'))
        u_expr = self.get_expression("u_usys", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert usys: {}".format(val/p))
        res.store("Uncertainty", "u_usys", np.absolute(val/p), "1")

    def uncert_m_cal(self, res):
        """Calculates the uncertainty of m_cal

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('m_cal'))
        u_expr = self.get_expression("u_m_cal", "kg")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert m_cal: {}".format(val/p))
        res.store("Uncertainty", "u_m_cal", np.absolute(val/p), "1")

    def uncert_r_cal(self, res):
        """Calculates the uncertainty of r_cal

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r_cal'))
        u_expr = self.get_expression("u_r_cal", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert r_cal: {}".format(val/p))
        res.store("Uncertainty", "u_r_cal", np.absolute(val/p), "1")

    def uncert_r_cal0(self, res):
        """Calculates the uncertainty of r_cal0

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r_cal0'))
        u_expr = self.get_expression("u_r_cal0", "lb")

        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert r_cal0: {}".format(val/p))
        res.store("Uncertainty", "u_r_cal0", np.absolute(val/p), "1")

    def uncert_g(self, res):
        """Calculates the uncertainty of m_cal

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('g'))
        u_expr = self.get_expression("u_g", "1")
        v_expr = self.Cons.get_expression("g", "m/s^2")

        f     = sym.lambdify(self.symb, s_expr * u_expr * v_expr, "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert g: {}".format(val/p))
        res.store("Uncertainty", "u_g", np.absolute(val/p), "1")

    def uncert_A(self, res):
        """Calculates the uncertainty of effective area

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('A'))
        u_expr = self.get_expression("u_A", "m^2")


        f     = sym.lambdify(self.symb, s_expr * u_expr, "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert A: {}".format(val/p))
        res.store("Uncertainty", "u_A", np.absolute(val/p), "1")

    def uncert_T(self, res):
        """Calculates the uncertainty of the temperature correction

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('T'))
        u_expr = self.get_expression("u_t", "C")


        f     = sym.lambdify(self.symb, s_expr * u_expr, "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert T: {}".format(val/p))
        res.store("Uncertainty", "u_T", np.absolute(val/p), "1")

    def uncert_rho_gas(self, res):
        """Calculates the uncertainty of the buoyancy correction

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        pconv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        ## --rho gas--
        # T in K
        Tconv   = self.Cons.get_conv("C", "K")
        T       = res.pick("Temperature", "frs5", "C") + Tconv
        gas     = self.get_gas()
        M       = np.full(self.no_of_meas_points, self.Cons.get_mol_weight(gas, "kg/mol"))
        # R in mbar m^3/mol/K
        R       = np.full(self.no_of_meas_points, self.Cons.get_value("R", "Pa m^3/mol/K") *pconv)

        s_expr  = sym.diff(self.model, sym.Symbol('rho_gas'))
        u_expr  = self.get_expression("u_rho_gas", "kg/m^3")
        f_u     = sym.lambdify((
                            sym.Symbol('M'),
                            sym.Symbol('R'),
                            sym.Symbol('T'),
                            sym.Symbol('p')), u_expr, "numpy")

        f_s     = sym.lambdify(self.symb, s_expr, "numpy")
        val     = f_s(*self.val_arr)*f_u(M,R,T,p)*pconv

        self.log.debug("uncert rho_gas: {}".format(val/p))
        res.store("Uncertainty", "u_rho_gas", np.absolute(val/p), "1")

    def uncert_rho_frs(self, res):
        """Calculates the uncertainty of the buoyancy correction for the piston.

        .. note::

                In order to avoid an uncertainty value of 0 the value 0
                for rho_gas (used during
                calculation) is replaced by the value at p, N2 and 27°C:

                (28.013e-3/(296.0+5.)/8.314*100./2.)

        .. todo::

                lambdify s_expr with density!

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        pconv   = self.Cons.get_conv("Pa", self.unit)
        p       = res.pick("Pressure", "cal", self.unit)

        ## -- rho piston --


        #s_expr  = sym.diff(self.model, sym.Symbol('rho_frs'))
        #s_expr  = s_expr.subs(sym.Symbol('rho_gas'), dens)

        #u_expr  = self.get_expression("u_rho_frs", "kg/m^3")

        #f       = sym.lambdify(self.symb, s_expr * u_expr, "numpy")
        #val     = f(*self.val_arr)*pconv
        val = np.full(self.no_of_meas_points, 0.0)
        self.log.debug("uncert rho_frs: {}".format(val/p))
        res.store("Uncertainty", "u_rho_frs", np.absolute(val/p), "1")

    def uncert_ab(self, res):
        """Calculates the uncertainty temperature expansion coefficient

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "cal", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r'))
        u_expr = self.get_expression("u_ab", "1/K")



        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert ab: {}".format(val/p))
        res.store("Uncertainty", "u_ab", np.absolute(val/p), "1")


    def offset(self, res):
        """Calculates the standard deviation of the *single* value of the 
        offset sample stored in ``Measurement.AuxValues.Pressure``
        
        .. todo::

            anselm needs to store the range a pressure point is measured with

        """
        off_std = np.full(self.no_of_meas_points, np.nan)
        p_ind_corr = res.pick("Pressure", "ind_corr", self.unit)
        range_arr = self.Range.get_str('ind')
        
        for i, r in enumerate(range_arr): 
            val, unit = self.Aux.get_value_and_unit(self.range_trans[r])
            conv = self.Cons.get_conv(from_unit=unit, to_unit=self.unit)
            off_std[i] = np.nanstd(val) *conv

        res.store("Uncertainty", "offset", off_std/p_ind_corr, "1")

    def repeat_rel(self, res):

        p_list = res.pick("Pressure", "ind_corr", "mbar")
        u = np.asarray([np.piecewise(p, [p <= 0.10, p <= 9.50, p > 9.50], [0.0008, 0.0003, 0.0001]).tolist() for p in p_list])

        res.store("Uncertainty", "repeat", u, "1")

    def total(self, res):
        
        p_cal = res.pick("Pressure", "cal", self.unit)

        p_ind = res.pick("Pressure", "ind", self.unit)

        offset_uncert = res.pick("Uncertainty", "offset", "1")
        repeat_uncert = res.pick("Uncertainty", "repeat", "1")
        standard_uncert = res.pick("Uncertainty", "frs5_total_rel", "1")
        # digitizing error still missing
        u_ind_abs = np.sqrt(np.power(p_cal * repeat_uncert, 2) + np.power(p_cal * offset_uncert, 2))

        u_rel = np.abs(p_ind / p_cal) * np.sqrt(np.power(u_ind_abs / p_ind, 2) + np.power(standard_uncert, 2))
        
        
        res.store("Pressure", "cal", p_cal , self.unit)
        res.store("Uncertainty", "total_rel", u_rel , "1")
        res.store("Uncertainty", "total_abs", u_rel*p_cal , self.unit)

