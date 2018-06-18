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
        conv   = self.Cons.get_conv(self.unit, "Pa")

        p_res = res.pick("Pressure", "dkmppc4_res", self.unit)
        p_cal = res.pick("Pressure", "dkm_ppc4", self.unit)


        p_res_pa = p_res*conv
        p_cal_pa = p_cal*conv

        u = (0.2 + 1.6e-5 * p_cal_pa + 0.5*p_res_pa) / p_cal_pa / 2

        res.store("Uncertainty", "dkm_ppc4_total_rel", u, "1")
        res.store("Uncertainty", "dkm_ppc4_total_abs", u*p_cal, self.unit)
        self.log.debug("uncert total: {}".format(u))
