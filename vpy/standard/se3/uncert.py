import numpy as np
import sympy as sym

from .std import Se3

class Uncert(Se3):

    def __init__(self, doc):
        super().__init__(doc)
        self.log.debug("init func: {}".format(__name__))

    def uncert_total(self,res):
        self.gen_val_dict(res)
        self.gen_val_array(res)

        self.uncert_v_start(res)

    def uncert_v_start(self, res):
        """Calculates the uncertainty of the starting volume

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f         = self.get_expansion()
        u_V_start = np.full(self.no_of_meas_points, np.nan)

        idxs = np.where(f == "f_s")
        if len(idxs) > 0:
            u_V_start[idxs] = self.get_value("u_V_s","cm^3")

        idxm = np.where(f == "f_m")
        if len(idxm) > 0:
            u_V_start[idxm] = self.get_value("u_V_m","cm^3")

        idxl = np.where(f == "f_l")
        if len(idxl) > 0:
            u_V_start[idxl] = self.get_value("u_V_l","cm^3")


        s_expr = sym.diff(self.model, sym.Symbol('V_start'))
        print(s_expr)
        print(self.val_arr)
        u      = sym.lambdify(self.symb, s_expr * u_V_start, "numpy")

        val   = u(*self.val_arr)
        res.store("Uncertainty", "u_V_start", np.absolute(val),self.unit)
        self.log.debug("uncert u_V_start: {}".format(val))
