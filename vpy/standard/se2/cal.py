import numpy as np
import sympy as sym
from ...values import Values, Temperature, Pressure, Date
from .std import Se2
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

class Cal(Se2):

    def __init__(self, doc):
        super().__init__(doc)

        self.Val = Values(doc)
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Date = Date(doc)
        self.CFaktor = Values(doc['Calibration']['Measurement']['Values']['faktor'])
        self.Range = doc['Calibration']['Measurement']['Values'].get('range',{})
        self.pressure_unit = "Pa"
        self.error_unit = "%"

    def get_expansion(self):
        """Returns an np.array

        :returns: array of expansion names
        :rtype: np.array of strings
        """
        pass

    
    def temperature_after(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_after_val, T_after_unit = self.Temp.get_value_and_unit("T_after")
        T_after_val = T_after_val + self.Cons.get_conv(T_after_unit, "K")
        ana.store("Temperature", "after", T_after_val, "K")
        ana.store("Temperature", "gas", T_after_val, "K")


    def temperature_room(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        T_room_val, T_room_unit = self.Temp.get_value_and_unit("T_room")
        T_room_val = T_room_val + self.Cons.get_conv(T_room_unit, "K")
        ana.store("Temperature", "room", T_room_val, "K")
    
    
    def pressure_cal(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cal_val, p_cal_unit = self.Pres.get_value_and_unit("p_cal")
        p_cal_val = p_cal_val * self.Cons.get_conv(p_cal_unit, self.pressure_unit)
        ana.store("Pressure", "cal", p_cal_val, self.pressure_unit)


    def pressure_ind(self, ana):
        """Simple translation from Measurement to Analysis
           "ind" = "p_cor" != "p_ind"   !!!!

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_cor_val, p_cor_unit = self.Pres.get_value_and_unit("p_cor")
        p_cor_val = p_cor_val * self.Cons.get_conv(p_cor_unit, self.pressure_unit)
        ana.store("Pressure", "ind_corr", p_cor_val, self.pressure_unit)


    def faktor(self, ana):
        """Simple translation from Measurement to Analysis
           "ind" = "p_cor" != "p_ind"   !!!!

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        _, p_ind_unit = self.Pres.get_value_and_unit("p_ind")
        _, p_cor_unit = self.Pres.get_value_and_unit("p_cor")
        cf = self.CFaktor.get_value("faktor","")
        if p_cor_unit==p_ind_unit:
            unit = "1"
        else:
            unit = "{to_unit}/{from_unit}".format(to_unit=p_cor_unit, from_unit=p_ind_unit)
        ana.store("Faktor", "faktor", cf, unit)

    def range(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        if self.Range != {}:
            r = self.Range['Value']
            ana.store("Range", "range", r, "1")
        else:
            pass

    def pressure_offset(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_off_val, _ = self.Pres.get_value_and_unit("p_offset")
        cf = self.CFaktor.get_value("faktor","")
        p_off_val = p_off_val * cf

        _, p_cor_unit = self.Pres.get_value_and_unit("p_cor")
        p_off_val = p_off_val * self.Cons.get_conv(p_cor_unit, self.pressure_unit)

        ana.store("Pressure", "offset", p_off_val, self.pressure_unit)


    def pressure_indication_error(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_ind = ana.pick("Pressure", "ind_corr",self.pressure_unit)
        p_cal = ana.pick("Pressure", "cal", self.pressure_unit)
        error = (p_ind - p_cal) / p_cal

        ana.store("Error", "ind", error, "1")


    def measurement_time(self, ana):
        """Simple translation from Measurement to Analysis

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        time = self.Date.parse_labview_date()
        ana.store("Date", "measurement", time, "date")


    def make_main_maesurement_index(self, ana):
        """Collects indices of the main measurement in average_index.

        :returns: list of indices
        :rtype: list
        """

        idx = self.Val.flatten(ana.average_index)
        mdate0 = ana.get_object("Type","measurement")["Value"]
        mdate = np.take(mdate0, idx).tolist()
        occurrences = [[i, mdate.count(i)] for i in list(set(mdate))]
        max_occurrence = sorted(occurrences, key=lambda j: j[1])[-1][0]
        idx = [i for i in idx if mdate0[i] == max_occurrence]

        ana.main_maesurement_index = idx

