import numpy as np
import sympy as sym
from .std import Se2

class Uncert(Se2):

    def __init__(self, doc):
        super().__init__(doc)

    def total(self, res):
        """Calculates the total uncertainty.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        pass

    def temperature_vessel(self, res):
        """Calculates the uncertainty of the temperature of the vessel.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        pass
