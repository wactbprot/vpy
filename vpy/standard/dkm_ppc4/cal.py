import numpy as np
import sympy as sym
from datetime import datetime
from .std import DkmPpc4


class Cal(DkmPpc4):

    def __init__(self, doc):
        super().__init__(doc)

    def pressure_cal(self, res):
        """Calculates the calibration pressure and stores the
        result under the path *Pressure, cal, mbar*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """


        p_res = res.pick("Pressure", "dkmppc4_res", self.unit)
        m = res.pick("Mass", "total", "kg")
        corr = res.pick("Correction", "temperature", "1")

        g = self.get_value("g_dkmppc4", "m/s^2")
        A = self.get_value("A_0_dkmppc4", "m^2")
        conv = self.Cons.get_conv("Pa", self.unit)
        p_cal = g * m / (A * corr) * conv + p_res

        res.store("Pressure", "cal", p_cal, self.unit)

    def pressure_res(self, res):
        """Transfers the pressure above the piston.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        p_res = self.Pres.get_value("dkmppc4_res", "mbar")
        conv = self.Cons.get_conv(from_unit="mbar",to_unit=self.unit)
        res.store("Pressure", "dkmppc4_res", p_res*conv, self.unit)

    def mass_total(self, res):
        """Transfers the total mass applied to the piston.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        m_tot = self.Mass.get_value("total", "kg")
        res.store("Mass", "total", m_tot, "kg")

    def temperature(self, res):
        """Transfers the temperature of the balance for the
        correction of the effective area.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        t_piston = self.Temp.get_value("dkmppc4", "C")
        res.store("Temperature", "dkmppc4", t_piston, "C")

    def temperature_correction(self, res):
        """Calculates the correction of the effective area.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        ab = self.get_value("alpha_beta_dkmppc4", "1/C")
        t_piston = res.pick("Temperature", "dkmppc4", "C")
        corr = 1.0 + ab * (t_piston - 20.0)

        res.store("Correction", "temperature", corr, "1")
