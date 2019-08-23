import numpy as np
import sympy as sym

from .std import DkmPpc4

class Uncert(DkmPpc4):

    def __init__(self, doc):
        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def total(self, res):
        """Calculates the total uncertainty.

        .. todo::
            store uncertainty expression in database document

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        self.pressure_res(res)
        self.pressure_cal(res)
        self.longterm(res)

        p_cal = res.pick("Pressure", "cal", self.unit)

        u = (res.pick("Uncertainty", "u_res", "1")**2
              + res.pick("Uncertainty", "u_cal", "1")**2
              + res.pick("Uncertainty", "u_lt", "1")**2
              )**0.5

        res.store("Uncertainty", "standard", u, "1")
        self.log.debug("uncert total: {}".format(u))

    def pressure_res(self, res):
        """Calculates the uncertainty contribution of the residual pressure.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv2Pa = self.Cons.get_conv(self.unit, "Pa")
        conv = self.Cons.get_conv("Pa", self.unit)

        p_res = res.pick("Pressure", "dkmppc4_res", self.unit) * conv2Pa
        p_cal = res.pick("Pressure", "cal", self.unit)
 
        u_expr = self.get_expression("u_p_res", "Pa")
        f = sym.lambdify(sym.Symbol('p_res'), u_expr , "numpy")

        u = f(p_res) * conv / p_cal

        res.store("Uncertainty", "u_res", u, "1")
        self.log.debug("relative uncert residual pressure : {}".format(u))

    def longterm(self, res):
        """Calculates the uncert. contrib of the longterm stability

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        u = self.get_value_full("u_lt", "1", self.no_of_meas_points)

        res.store("Uncertainty", "u_lt", u, "1")
        self.log.debug("relative uncert longterm stab.: {}".format(u))

    def pressure_cal(self, res):
        """Calculates the uncertainty contribution of the calibration of the device.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv2Pa = self.Cons.get_conv(self.unit, "Pa")

        p_cal = res.pick("Pressure", "cal", self.unit)* conv2Pa
        u_expr = self.get_expression("u_p_cal", "Pa")
        f = sym.lambdify(sym.Symbol('p_cal'), u_expr , "numpy")
        u = f(p_cal) / p_cal # Pa/Pa

        res.store("Uncertainty", "u_cal", u, "1")
        self.log.debug("relative uncert of calibration: {}".format(u))
