import numpy as np
import sympy as sym
from ..device.device import Device


class Qbs(Device):

    def __init__(self, doc, dev):
        super().__init__(doc, dev)

        self.log.debug("init func: {}".format(__name__))

    def get_name(self):
        return self.doc['Name']

    def get_error_correction(self, p, punit, runit):
        """Calculates the error of indication by means of the expression stored

        :param p: p pressure to calculate the error
        :type p: np.array
        :param punit: punit pressure unit
        :type punit: str
        :param runit: runit unit of values returned
        :type runit: str
        """

        e_expr = self.get_expression("e", "%")
        f      = sym.lambdify(sym.Symbol('p'), e_expr, "numpy")
        return f(p)
