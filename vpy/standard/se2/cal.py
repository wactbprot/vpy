import numpy as np
import sympy as sym
<<<<<<< HEAD
from ...values import Temperature, Pressure, Date
=======
from ...values import Temperature, Pressure, Time
>>>>>>> 42aa63841f1bb5d4a8b0ed801e611333d00d612b
from .std import Se2

class Cal(Se2):

    def __init__(self, doc):
        super().__init__(doc)

        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
<<<<<<< HEAD
        self.Date = Date(doc)
=======
        self.t = Time(doc)

>>>>>>> 42aa63841f1bb5d4a8b0ed801e611333d00d612b
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

        p_cal = self.Pres.get_value("p_cal", " mbar")
        res.store("Pressure", "cal", p_cal, "mbar")


    def pressure_ind(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cor = self.Pres.get_value("p_cor", " mbar")
        res.store("Pressure", "ind", p_cor, "mbar")


    def pressure_offset(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_off = self.Pres.get_value("p_offset", " mbar")
        res.store("Pressure", "offset", p_off, "mbar")

    def measurement_time(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        time = self.t.get_value("Date", None)
        res.store("Time", "t", time, None)