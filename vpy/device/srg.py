import numpy as np
from .device import Device

class Srg(Device):
    """ SRG
    The fix_total_relative_uncertainty is used for the calculation of the
    uncertainty of the corrected slope.
    """

    def __init__(self, doc, dev):
        super().__init__(doc, dev)

        self.total_relative_uncertainty_k2 = 2.6e-3
        self.log.debug("init func: {}".format(__name__))

    def get_name(self):
        return self.doc['Name']

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

    def pressure(self, pressure_dict, temperature_dict, unit= "Pa", gas= "N2"):
        """Calculates the presssure by means of dcr_conversion.
        Returns the pressure in the given unit.
        """
       
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float) # np.array also converts None to na
      

        if pressure_unit == "DCR":
            dcr_conv = self.dcr_conversion(unit, gas)
            self.log.debug(dcr_conv)
            
            temp_corr = self.temperature_correction(temperature_dict)
            self.log.debug(temp_corr)

            pressure = pressure_value * dcr_conv  *temp_corr
        else:
            pressure = pressure_value * self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)
        
        return pressure

    def sigma_null(self, p_cal, cal_unit, p_ind, ind_unit, k = 2):
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
        if cal_unit == ind_unit:
            x = p_cal
            y = p_ind/p_cal
        else:
            self.log.error("units don't match!")
            return None, None, None
          
        if not len(x) == len(y):
            self.log.error("length don't match!")
            return None, None, None
            
        n = len(x)
        avr_x = np.sum(x)/n
        avr_y = np.sum(y)/n

        m = np.sum((x - avr_x) * (y - avr_y))/np.sum((x - avr_x)**2)
        b = avr_y - m * avr_x
        
        var_s = np.sum((y - b - m * x)**2)/(n-2)
        
        var_b = var_s * np.sum(x**2) / (n * np.sum((x - avr_x)**2))
        var_m = var_s * 1.0 / np.sum((x - avr_x)**2)

        sens_b = (m / b**2)
        sens_m = (1.0 / b)
       
        u = k * (sens_m**2 * var_m  + sens_b**2 * var_b +  (self.total_relative_uncertainty_k2/2.0 * m/b)**2)**0.5
       
       
        return b, m, u
