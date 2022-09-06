import numpy as np
import sympy as sym
from ..device.device import Device
from ..constants import Constants

class Ig(Device):
    rel_repeat_uncert = 0.008
    resolution = 0.02

    def __init__(self, doc, dev):
        self.Const = Constants(doc)
        super().__init__(doc, dev)

    def pressure(self, pressure_dict, unit='Pa'):
        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float)

        return pressure_value * self.Const.get_conv(pressure_unit, unit)

    def get_name(self):
        return self.doc['Name']

    def offset_uncert(self, ana,  reject_index = None, ind_unit=None):
        """
        The offset uncertainty is calculated by means of `np.diff(offset)`.
        Drift influences are avoided.
        """
        if ind_unit is None:
            ind_unit = ana.pressure_unit

        ind = ana.pick("Pressure", "ind_corr", ind_unit)
        cal = ana.pick("Pressure", "cal", ind_unit)
        offset = ana.pick("Pressure", "ind_offset", ind_unit)

        if reject_index:
            for i in reject_index:
                ind[i] = np.nan
                offset[i] = np.nan

        ##
        u_rel_arr = np.full(len(ind), np.nan)
        u_abs_arr = np.full(len(ind), np.nan)
        offset_contrib = {"Unit": ind_unit}

        ## Das Saugvermögen der KP wird mit steigender N2-Belegung bis zu
        ## einem p_cal=3e-7mbar größer; der Offset sinkt während der Kalib.
        ## Es soll deshalb nur die Hälfte des delta offset als Unsicherheit
        ## angesetzt werden
        m = np.nanmean(np.abs(np.diff(offset)))/2.0

        if m == 0.0:
            m = self.ask_for_offset_uncert(offset, ind_unit, range_str="all")

        offset_contrib["all"] = m
        u_abs_arr = m

        ana.store_dict(quant='AuxValues', d={'OffsetUncertContrib': offset_contrib}, dest=None)
        ana.store("Uncertainty", "offset",  m/ind, "1")

    def repeat_uncert(self, ana, ind_unit=None):
        if ind_unit is None:
            ind_unit = ana.pressure_unit

        u = ana.pick("Uncertainty", "uncertExpSd", "1")
        if u is None:
            u = self.rel_repeat_uncert

        p_ind = ana.pick("Pressure", "ind_corr", ind_unit)
        u_rel = np.full(len(p_ind), u)

        ana.store("Uncertainty", "repeat", u_rel, "1")

    def digit_uncert(self, ana, ind_unit=None):
        if ind_unit is None:
            ind_unit = ana.pressure_unit

        p_ind = ana.pick("Pressure", "ind", ind_unit)
        if ind_unit != "A":
            u = self.cal_abs_digit_uncert(p_ind, self.resolution)
        else:
            u = 0.

        ana.store("Uncertainty", "digit", u/p_ind, "1")

    def emis_current(self, unit):
        ie = self.get_value("ie", "mA")

        return ie * self.Const.get_conv(from_unit="mA", to_unit=unit)

    def emis_uncert(self, ana, ind_unit=None):
        if ind_unit is None:
            ind_unit = ana.pressure_unit

        u = self.get_value("uncertEmis", "1")
        p_ind = ana.pick("Pressure", "ind", ind_unit)

        ana.store("Uncertainty", "emis", np.full(len(p_ind), u), "1")

    def coll_uncert(self, ana, ind_unit=None):

        u1 = self.get_value("uncertOffset", ind_unit)
        u2 = self.get_value("uncertOffsetDrift", ind_unit)
        i = ana.pick("Pressure", "ind", ind_unit)

        ana.store("Uncertainty", "offset", np.sqrt(np.power(u1/i, 2) + np.power(u2/i, 2)), "1")
