import numpy as np
import pandas as pd
import sympy as sym
from ...values import Temperature, Pressure
from .std import Se2

class Cal(Se2):

    def __init__(self, doc):
        super().__init__(doc)

        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)

        self.log.debug("init func: {}".format(__name__))


    def get_expansion(self):
        """Returns an np.array


        :returns: array of expansion names
        :rtype: np.array of strings
        """
        pass


    def pressure_cal(self, res):
        """Simple translation foem Measurement to Analysis


        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        # p_todo = self.ToDo.get_value("target", "mbar")
        p_cal = self.Pres.get_value("p_cal", " mbar")
        p_cor = self.Pres.get_value("p_cor", " mbar")

        key = self.Pres.round_to_n(p_cal, 2)

        p_cal = [np.mean(g.values.tolist()) for _, g in pd.DataFrame(p_cal).groupby(key)]

        p_cor = [np.mean(g.values.tolist()) for _, g in pd.DataFrame(p_cor).groupby(key)]
       
        res.store("Pressure", "cal", p_cal, "mbar")
        res.store("Pressure", "cor", p_cor, "mbar")

