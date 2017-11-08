import numpy as np
from .device import Device
from ..vpy_io import Io

class Srg(Device):
    """ SRG
    """

    io = Io()
    log = io.log(__name__)
    log.info("start logging")
    def __init__(self, doc, dev):
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']

    def dcr_conversion(self, unit="mbar", gas="N2"):
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
        sgm = self.get_value("sigma_eff_" + gas, "1")
        d   = self.get_value("d", "m")

        R   = self.Const.get_value("R", "Pa m^3/mol/K")
        T   = self.Const.get_value("referenceTemperature", "K")
        M   = self.Const.get_value("molWeight_" + gas, "kg/mol")

        conv = self.Const.get_conv("Pa", unit)
        return np.sqrt(8*R*T/(np.pi*M))*np.pi*d*rho/20*conv/sgm

    def pressure(self, P, T, unit= "mbar", gas= "N2"):
        """Calculates the presssure by means of dcr_conversion.
        Returns the pressure in the given unit.
        """
        t_ref = self.Const.get_value("referenceTemperature", "K")

        if T['Unit'] == "K":
            t_srg = T['Value']

        if T['Unit'] == "C":
            conv_t = self.Const.get_conv(T['Unit'], "K")
            t_srg = T['Value'] + conv_t

        corr_t = np.sqrt(t_srg/t_ref)

        if P['Unit'] == "DCR":
            conv_p = self.dcr_conversion(unit, gas)

        return P['Value'] * conv_p * corr_t
