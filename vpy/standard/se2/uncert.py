import numpy as np
import sympy as sym

from .std import Frs5

class Uncert(Frs5):


    def __init__(self, doc):
        super().__init__(doc)
        self.log.debug("init func: {}".format(__name__))

    def total(self, res):
        """Calculates the total uncertainty.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

    def uncert_temperature(self, res):
        """Calculates the uncertainty of the temperature correction.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
