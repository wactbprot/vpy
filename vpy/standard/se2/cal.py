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

        T_after_val, T_after_unit = self.Temp.get_value_and_unit("T_after")
        T_after_val = T_after_val + self.Cons.get_conv(T_after_unit, "C")
        res.store("Temperature", "after", T_after_val, "C")


    def temperature_room(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_room_val, T_room_unit = self.Temp.get_value_and_unit("T_room")
        T_room_val = T_room_val + self.Cons.get_conv(T_room_unit, "C")
        res.store("Temperature", "room", T_room_val, "C")
    
    
    def pressure_cal(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cal_val, p_cal_unit = self.Pres.get_value_and_unit("p_cal")
        p_cal_val = p_cal_val * self.Cons.get_conv(p_cal_unit, "mbar")
        res.store("Pressure", "cal", p_cal_val, "mbar")


    def pressure_ind(self, res):
        """Simple translation from Measurement to Analysis
           "ind" = "p_cor" != "p_ind"   !!!!

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cor_val, p_cor_unit = self.Pres.get_value_and_unit("p_cor")
        p_cor_val = p_cor_val * self.Cons.get_conv(p_cor_unit, "mbar")
        res.store("Pressure", "ind", p_cor_val, "mbar")


    def pressure_conversion_factor(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_ind_val, p_ind_unit = self.Pres.get_value_and_unit("p_ind")
        p_off_val, _ = self.Pres.get_value_and_unit("p_offset")
        p_cor_val, p_cor_unit = self.Pres.get_value_and_unit("p_cor")
        cf = p_cor_val / (p_ind_val - p_off_val)

        res.store("Pressure", "cf", cf, p_cor_unit + "/" + p_ind_unit)


    def pressure_offset(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_off_val, _ = self.Pres.get_value_and_unit("p_offset")
        cf = res.get_object("Type", "cf")["Value"]
        p_off_val = [0 if p_off_val[i] == 0 else p_off_val[i] * cf[i] for i in range(len(p_off_val))]

        res.store("Pressure", "offset", p_off_val, "mbar")


    def measurement_time(self, res):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        time = self.Date.parse_labview_date()
        res.store("Date", "measurement", time, "date")







        