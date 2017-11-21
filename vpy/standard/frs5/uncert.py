import numpy as np
import sympy as sym

from .std import Frs5
from ...vpy_io import Io

class Uncert(Frs5):


    def __init__(self, doc):
        super().__init__(doc)

        io = Io()
        self.log = io.logger(__name__)
        self.log.debug("init func: {}".format(__name__))

    def total(self, res):
        """Calculates the total uncertainty.
        sympy derives the sensitivity coefficients.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        self.define_model(res)
        self.gen_val_array(res)
        self.uncert_r(res)
        self.uncert_r_zc(res)
        self.uncert_r_zc0(res)
        self.uncert_ub(res)
        self.uncert_usys(res)
        self.uncert_m_cal(res)
        self.uncert_g(res)
        self.uncert_A(res)
        #
        #

        #    s_A          = sym.diff(p_frs, A)
        #    s_tem        = sym.diff(p_frs, tem)
        #    s_tem        = sym.diff(p_frs, tem)
        #    s_rho_gas    = sym.diff(p_frs, rho_gas)
        #    s_rho_frs    = sym.diff(p_frs, rho_frs)
        #
        #    u_A       = self.get_expression("u_A", "m^2")
        #    u_m_cal   = self.get_expression("u_m_cal", "kg")
        #    u_rho_frs = self.get_expression("u_rho_frs", "kg/m^3")
        #
        #    # relative uncertainties
        #    u_g      = self.get_expression("u_g", "1") * self.g
        #
        #    # gas dependend
        #    gas = self.get_gas()
        #    u_rho_gas  = self.get_expression("u_rho_frs", "kg/m^3")
        #
        #
        #    s_r_cal      = sym.diff(self.model, r_cal)
        #    s_r_cal0     = sym.diff(self.model, r_cal0)
        #
        #    u_r_cal   = self.get_expression("u_r_cal", "lb")
        #    u_r_cal0  = self.get_expression("u_r_cal0", "lb")


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

        self.log.debug("uncert r: {}".format(val/p))
        res.store("Uncertainty", "r", np.absolute(val/p), "1")

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
        res.store("Uncertainty", "r_zc", np.absolute(val/p), "1")

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
        res.store("Uncertainty", "r_zc0", np.absolute(val/p), "1")

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
        res.store("Uncertainty", "ub", np.absolute(val/p), "1")

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
        res.store("Uncertainty", "usys", np.absolute(val/p), "1")

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
