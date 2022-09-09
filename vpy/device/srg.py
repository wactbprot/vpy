import sys
import numpy as np
from .device import Device
from ..constants import Constants

class Srg(Device):
    """ SRG
    The fix_total_relative_uncertainty is used for the calculation of the
    uncertainty of the corrected slope.
    """
    unit = "Pa"
    sigma_min_pressure = 0.09
    sigma_max_pressure = 1.5
    total_relative_uncertainty_k2 = 2.6e-3 ## workaround

    def __init__(self, doc, dev):
        self.Const = Constants(doc)
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc.get("Name")

    def make_sigma_index(self, p_cal, unit):
        """Replaces the `ToDo.make_average_index()`
        since all pressures in the range `p_cal[i] > min_p and p_cal[i] < max_p`
        should be used to calculate the `sigma`.
        """
        if unit != self.unit:
            sys.exit("implement me!")
        N = len(p_cal)
        min_p = self.sigma_min_pressure
        max_p = self.sigma_max_pressure

        return [[i] for i in range(N) if p_cal[i] > min_p and p_cal[i] < max_p]

    def dcr_conversion(self, unit="Pa", gas="N2"):
        """
        Calculates the conversion constant :math:`K` between DCR and
        unit by means of

        :math:`K = \\sqrt{ \\frac{ 8 R T }{ \\pi M}} \\pi d \\rho /20`

        :param unit: unit unit
        :type unit: str
        :param gas: gas gas
        :type gas: str
        :return: conversion factor between DCR and unit
        :rtype: float
        """
        rho = self.get_value("rho","kg/m3")
        if rho is None:
            conv_m = self.Const.get_conv(from_unit='g', to_unit='kg')
            conv_V = self.Const.get_conv(from_unit='cm^3', to_unit='m^3')
            rho = self.get_value("Density","g/cm^3")*conv_m/conv_V

        d   = self.get_value("d", "m")
        if d is None:
            conv_s = self.Const.get_conv(from_unit='mm', to_unit='m')
            d  = self.get_value("Diameter", "mm") * conv_s

        R   = self.Const.get_value("R", "Pa m^3/mol/K")
        T   = self.Const.get_value("referenceTemperature", "K")
        M   = self.Const.get_value("molWeight_" + gas, "kg/mol")

        conv = self.Const.get_conv("Pa", unit)

        return np.sqrt(8*R*T/(np.pi*M))*np.pi*d*rho/20*conv

    def temperature_correction(self, temperature_dict):
        """Calculates the temperature correction to the reference temperature
        """
        reference_temperature = self.Const.get_value("referenceTemperature", "K")
        temperature_unit = temperature_dict.get('Unit')

        srg_temperature = np.array(temperature_dict.get('Value'), dtype=np.float)
        if temperature_unit == "C":
            conv = self.Const.get_conv(from_unit='C', to_unit='K')
            srg_temperature += conv

        return  np.sqrt(srg_temperature/reference_temperature)

    def pressure(self, pressure_dict, temperature_dict, range_dict=None, unit= "Pa", gas= "N2"):
        """Calculates the presssure by means of dcr_conversion.
        Returns the pressure in the given unit.
        """

        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float) # np.array also converts None to na


        if pressure_unit == "DCR":
            dcr_conv = self.dcr_conversion(unit, gas)
            temp_corr = self.temperature_correction(temperature_dict)
            pressure = pressure_value * dcr_conv  * temp_corr
        else:
            pressure = pressure_value * self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)

        return pressure

    def sigma_null(self, p_cal, cal_unit, p_ind, ind_unit):
        """
        https://de.wikipedia.org/wiki/Lineare_Einfachregression
        k = coverage factor
        x ... p_cal
        y ... sigma
        m ... slope
        b ... sigma_0
        var_m ... var(m)
        var_b ... var(b)
        u ... u(m/sigma_0)

        print(sens_m * var_m**0.5)
        print(sens_b * var_b**0.5)
        print(var_m**0.5)
        print(var_b**0.5)
        print((self.total_relative_uncertainty_k2/2.0 * m/b))
        print((self.total_relative_uncertainty_k2/2.0 * b * sens_b))

        python script/se3/se3_cal_result.py --ids 'cal-2019-se3-kk-75138_0001' --db 'vl_db' --srv 'http://a73434.berlin.ptb.de:5984'
        0.0001747977356194887
        -1.954144020125424e-06
        0.0001720421398635844
        0.00011476238813591167
        -2.17870974810604e-05
        -2.1787097481060404e-05
        """

        conv = self.Const.get_conv(from_unit=ind_unit, to_unit=cal_unit)
        p_ind = p_ind * conv
        x = p_cal
        y = p_ind/p_cal

        m, b, var_m, var_b = self.Vals.lin_reg(x, y)
        #print(m)
        #print(b)
        #print(var_m)
        #print(var_b)
        sens_b = (m / b**2)
        sens_m = (1.0 / b)

        u = (sens_m**2 * var_m  + sens_b**2 * var_b +  (self.total_relative_uncertainty_k2/2.0 * m/b)**2)**0.5
        #print(u)
        return b, m, u

    def uncert_sigma_eff(self, ana):
        """Uncertainty estimation based on
         http://intranet.ptb.de/fileadmin/dokumente/intranet/qualitaetsmanagement/Fachabteilungen/Abt7/FB75/7.5-AA-SE2_ausgabe5.pdf
         Seite 33: '10.3 Messunsicherheitsbudget für SRG'
         """
        sigma = ana.pick("Sigma", "eff", "1")
        N = len(sigma)
        u_rel = 4.0e-4

        ana.store("Uncertainty", "sigma_eff", np.full(N, u_rel), "1")

    def uncert_ind(self, ana):
        sigma = ana.pick("Sigma", "eff", "1")
        N = len(sigma)
        u_rel = 1.0e-4

        ana.store("Uncertainty", "ind", np.full(N, u_rel), "1")

    def uncert_temperature(self, ana):
        sigma = ana.pick("Sigma", "eff", "1")
        N = len(sigma)
        u_rel = 3.4e-4

        ana.store("Uncertainty", "temperature", np.full(N, u_rel), "1")

    def uncert_offset(self, ana):
        sigma = ana.pick("Sigma", "eff", "1")
        N = len(sigma)
        u_rel = 5.1e-5

        ana.store("Uncertainty", "offset", np.full(N, u_rel), "1")

    def uncert_repeat(self, ana):
        sigma = ana.pick("Sigma", "eff", "1")
        N = len(sigma)
        u_rel = 6.0e-4

        ana.store("Uncertainty", "repeat", np.full(N, u_rel), "1")


    def device_uncert(self, ana):
        u_1 = ana.pick("Uncertainty", "offset", "1")
        u_2 = ana.pick("Uncertainty", "repeat", "1")
        u_3 =  ana.pick("Uncertainty", "ind", "1")
        u_4 =  ana.pick("Uncertainty", "temperature", "1")
        u_5 =  ana.pick("Uncertainty", "sigma_eff", "1")

        u = np.sqrt(np.power(u_1, 2) +
                    np.power(u_2, 2) +
                    np.power(u_3, 2) +
                    np.power(u_4, 2) +
                    np.power(u_5, 2))
        ana.store("Uncertainty", "device", u, "1")
