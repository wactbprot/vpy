import numpy as np
import sympy as sym
from ..device.device import Device
from ..constants import Constants

class Qbs(Device):
    unit = "Pa"
    rel_repeat_uncert = 5e-5
    resolution = 0.1 # Pa

    def __init__(self, doc, dev):
        self.Const = Constants(doc)

        if 'CalibrationObject' in dev:
            dev = dev.get('CalibrationObject')

        super().__init__(doc, dev)

        dev_setup = dev.get('Setup')
        if dev_setup:
            use_from = dev_setup.get('UseFrom')
            use_to = dev_setup.get('UseTo')
            use_unit = dev_setup.get('UseUnit')

        if use_from and use_to and use_unit:
            conv = self.Const.get_conv(from_unit=use_unit, to_unit=self.unit)
            self.max_p = float(use_to) * conv
            self.min_p = float(use_from) * conv

        if 'Interpol' in dev:
            # pressure
            v, u = self.get_value_and_unit('p_ind')
            conv = self.Const.get_conv(from_unit=u, to_unit=self.unit)
            self.interpol_p = v * conv
            # error
            self.interpol_e = self.get_value(value_type='e', value_unit='1')

            interpol_min = np.min(self.interpol_p)
            interpol_max = np.max(self.interpol_p)

            if self.min_p > interpol_min:
                self.interpol_min = self.min_p
            else:
                self.interpol_min = interpol_min
            if self.max_p > interpol_max:
                self.interpol_max =  interpol_max
            else:
                self.interpol_max =  self.max_p

    def get_name(self):
        return self.doc['Name']

    def get_error_correction(self, p, punit, runit):
        """Calculates the error of indication by means of the expression stored

        :param p: p pressure to calculate the error
        :type p: np.array
        :param punit: punit pressure unit
        :type punit: str
        :param runit: runit unit of values returned
        :type runit: str
        """

        e_expr = self.get_expression("error", "%")
        f = sym.lambdify(sym.Symbol('p'), e_expr, "numpy")
        return f(p)

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
