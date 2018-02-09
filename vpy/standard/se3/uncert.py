import numpy as np
import sympy as sym

from .std import Se3

class Uncert(Se3):

    def __init__(self, doc):
        super().__init__(doc)
        self.log.debug("init func: {}".format(__name__))

    def uncert_v_start(self, res):
        """Calculates the uncertainty of the starting volume
        
        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        s_expr = sym.diff(self.model, sym.Symbol('r'))
        u_expr = self.get_expression("u_r", "lb")
        f     = sym.lambdify(self.symb, s_expr * u_expr , "numpy")

        val   = f(*self.val_arr)*conv
        res.store("Uncertainty", "u_r", np.absolute(val/p), "1")
        self.log.debug("uncert r: {}".format(val/p))
