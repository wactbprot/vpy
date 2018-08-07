import numpy as np
import sympy as sym
from ...values import Temperature, Pressure, Date
from .std import Se2

class Cal(Se2):

    def __init__(self, doc):
        super().__init__(doc)

        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Date = Date(doc)

    def get_expansion(self):
        """Returns an np.array

        :returns: array of expansion names
        :rtype: np.array of strings
        """
        pass

    
    def temperature_after(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_after = self.Temp.get_value("T_after", "C")
        res.store("Temperature", "after", T_after, "C")


    def temperature_room(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_room = self.Temp.get_value("T_room", "C")
        res.store("Temperature", "room", T_room, "C")
    
    
    def pressure_cal(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cal = self.Pres.get_value("p_cal", "mbar")
        res.store("Pressure", "cal", p_cal, "mbar")


    def pressure_ind(self, res):
        """Simple translation from Measurement to Analysis
           "ind" = "p_cor" != "p_ind"   !!!!

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cor = self.Pres.get_value("p_cor", "mbar")
        res.store("Pressure", "ind", p_cor, "mbar")


    def pressure_conversion_factor(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_ind = np.asarray(self.Pres.get_object("Type", "p_ind")["Value"])
        p_off = np.asarray(self.Pres.get_object("Type", "p_offset")["Value"])
        p_cor = self.Pres.get_value("p_cor", "mbar")
        cf = p_cor / (p_ind - p_off)

        res.store("Pressure", "cf", cf, "")


    def pressure_offset(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_off = np.asarray(self.Pres.get_object("Type", "p_offset")["Value"])
        cf = np.asarray(res.get_object("Type", "cf")["Value"])
        p_off = p_off * cf
        p_off = [0 if p_off[i] == 0 else p_off[i] * cf[i] for i in range(len(p_off))]

        res.store("Pressure", "offset", p_off, "mbar")


    def measurement_time(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        time = self.Date.parse_labview_date()
        res.store("Date", "measurement", time, "date")