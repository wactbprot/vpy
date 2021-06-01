import numpy as np
import sympy as sym
from ..device.device import Device
from ..constants import Constants

class Pir(Device):
    rel_repeat_uncert = 0.008
    resolution = 0.02

    def __init__(self, doc, dev):
        self.Const = Constants(doc)

        if dev:
            self.doc = dev
            self.conversion_type = dev.get('Setup').get('ConversionType')

        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']

    def pressure(self, pressure_dict, temperature_dict, range_dict=None, unit= 'Pa', gas= "N2"):

        pressure_unit = pressure_dict.get('Unit')
        pressure_value = np.array(pressure_dict.get('Value'), dtype=np.float)

        if pressure_unit == "V":
            if self.conversion_type == "ley_log":
                return (pressure_value + self.cmr_offset) * self.cmr_factor * self.cmr_base_factor[self.type_head]

            sys.exit("conversion type not implemented")
        else:
            return pressure_value * self.Const.get_conv(from_unit=pressure_unit, to_unit=unit)

    def offset_uncert(self, ana,  reject_index = None):
        """
        The offset uncertainty is calculated by means of `np.diff(offset)`.
        Drift influences are avoided.
        """

        ind = ana.pick("Pressure", "ind_corr", ana.pressure_unit)
        offset = ana.pick("Pressure", "offset", ana.pressure_unit)

        if reject_index:
            for i in reject_index:
                ind[i] = np.nan
                offset[i] = np.nan

        ##
        u_rel_arr = np.full(len(ind), np.nan)
        u_abs_arr = np.full(len(ind), np.nan)
        offset_contrib = {"Unit": ana.pressure_unit}

        m = np.nanmean(np.abs(np.diff(offset)))
        if m == 0.0:
            m = self.ask_for_offset_uncert(offset, ana.pressure_unit, range_str="all")

        offset_contrib["all"] = m
        u_abs_arr = m

        ana.store_dict(quant='AuxValues', d={'OffsetUncertContrib': offset_contrib}, dest=None)
        ana.store("Uncertainty", "offset",  m/ind, "1")

    def repeat_uncert(self, ana):

        p_ind = ana.pick("Pressure", "ind_corr", ana.pressure_unit)
        u_rel = np.full(len(p_ind), self.rel_repeat_uncert)

        ana.store("Uncertainty", "repeat", u_rel, "1")

    def digit_uncert(self, ana):

        p_ind = ana.pick("Pressure", "ind", ana.pressure_unit)
        u = self.cal_abs_digit_uncert(p_ind, self.resolution)

        ana.store("Uncertainty", "digit", u/p_ind, "1")
