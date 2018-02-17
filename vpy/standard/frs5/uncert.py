import numpy as np
import sympy as sym

from .std import Frs5

class Uncert(Frs5):

    def __init__(self, doc):
        super().__init__(doc)
        
        self.log.debug("init func: {}".format(__name__))

    def total(self, res):
        """Calculates the total uncertainty.
        sympy derives the sensitivity coefficients.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

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

        p = res.pick("Pressure", "frs5", self.unit)
        res.store("Uncertainty", "total_rel", u_total, "1")
        res.store("Uncertainty", "total_abs", u_total*p, self.unit)
        self.log.debug("uncert total: {}".format(u_total))


    def uncert_r(self, res):
        """Calculates the uncertainty of the r (reading)

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv   = self.Cons.get_conv("Pa", self.unit)
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

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
        p       = res.pick("Pressure", "frs5", self.unit)

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
        p      = res.pick("Pressure", "frs5", self.unit)

        s_expr = sym.diff(self.model, sym.Symbol('r'))
        u_expr = self.get_expression("u_ab", "1/K")



        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")
        val   = f(*self.val_arr)*conv

        self.log.debug("uncert ab: {}".format(val/p))
        res.store("Uncertainty", "u_ab", np.absolute(val/p), "1")
