import numpy as np
import copy
import sympy as sym
from .std import Ce3


class Cal(Ce3):
    np.warnings.filterwarnings('ignore')

    def __init__(self, doc):
        super().__init__(doc)

    def pressure_fill(self, ana):

        p_fill = np.full(self.no_of_meas_points, np.nan)
        e_fill = np.full(self.no_of_meas_points, np.nan)
        p_fill_offset = np.full(self.no_of_meas_points, np.nan)

        p_lw = np.full(self.no_of_meas_points, np.nan)
        e_lw = np.full(self.no_of_meas_points, np.nan)
        p_lw_offset = np.full(self.no_of_meas_points, np.nan)

        dp_before = self.Pres.get_value("dp_before", self.unit)
        dp_after = self.Pres.get_value("dp_after", self.unit)

        p_before = self.Pres.get_value("before_lw_fill", self.unit)
        p_after = self.Pres.get_value("after_lw_fill", self.unit)

        i_cdga_x001 = np.where(np.less_equal(p_before, self.cdga_lim_x001))
        i_cdga_x01  = np.where(np.logical_and(np.less_equal(p_before, self.cdga_lim_x01),
                                              np.greater(p_before, self.cdga_lim_x001)))
        i_cdga_x1   = np.where(np.logical_and(np.less_equal(p_before, self.cdga_lim_x1),
                                              np.greater(p_before, self.cdga_lim_x01)))

        i_cdgb_x001 = np.where(np.logical_and(np.less_equal(p_before, self.cdgb_lim_x001),
                                              np.greater(p_before, self.cdga_lim_x1)))

        i_cdgb_x01  = np.where(np.logical_and(np.less_equal(p_before, self.cdgb_lim_x01),
                                              np.greater(p_before, self.cdgb_lim_x001)))
        i_cdgb_x1   = np.where(np.logical_and(np.less_equal(p_before, self.cdgb_lim_x1),
                                              np.greater(p_before, self.cdgb_lim_x01)))

        if np.shape(i_cdga_x1)[1] > 0:
            p_offset = self.Aux.get_value("cdga_x1_offset", self.unit)[-1]

            p_fill[i_cdga_x1] = np.take(p_after, i_cdga_x1) - p_offset
            p_fill_offset[i_cdga_x1] = p_offset

            p_lw[i_cdga_x1] = np.take(p_before, i_cdga_x1) - p_offset
            p_lw_offset[i_cdga_x1] = p_offset

        if np.shape(i_cdga_x01)[1] > 0:
            p_offset = self.Aux.get_value("cdga_x0.1_offset", self.unit)[-1]

            p_fill[i_cdga_x01] = np.take(p_after, i_cdga_x01) - p_offset
            p_fill_offset[i_cdga_x01] = p_offset

            p_lw[i_cdga_x01] = np.take(p_before, i_cdga_x01) - p_offset
            p_lw_offset[i_cdga_x01] = p_offset

        if np.shape(i_cdga_x001)[1] > 0:
            p_offset = self.Aux.get_value("cdga_x0.01_offset", self.unit)[-1]

            p_fill[i_cdga_x001] = np.take(p_after, i_cdga_x001) - p_offset
            p_fill_offset[i_cdga_x001] = p_offset

            p_lw[i_cdga_x001] = np.take(p_before, i_cdga_x001) - p_offset
            p_lw_offset[i_cdga_x001] = p_offset

        if np.shape(i_cdgb_x1)[1] > 0:
            p_offset = self.Aux.get_value("cdgb_x1_offset", self.unit)[-1]

            p_fill[i_cdgb_x1] = np.take(p_after, i_cdgb_x1) - p_offset
            p_fill_offset[i_cdgb_x1] = p_offset

            p_lw[i_cdgb_x1] = np.take(p_before, i_cdgb_x1) - p_offset
            p_lw_offset[i_cdgb_x1] = p_offset

        if np.shape(i_cdgb_x01)[1] > 0:
            p_offset = self.Aux.get_value("cdgb_x0.1_offset", self.unit)[-1]

            p_fill[i_cdgb_x01] = np.take(p_after, i_cdgb_x01) - p_offset
            p_fill_offset[i_cdgb_x01] = p_offset

            p_lw[i_cdgb_x01] = np.take(p_before, i_cdgb_x01) - p_offset
            p_lw_offset[i_cdgb_x01] = p_offset

        if np.shape(i_cdgb_x001)[1] > 0:
            p_offset = self.Aux.get_value("cdgb_x0.01_offset", self.unit)[-1]

            p_fill[i_cdgb_x001] = np.take(p_after, i_cdgb_x001) - p_offset
            p_fill_offset[i_cdgb_x001] = p_offset

            p_lw[i_cdgb_x001] = np.take(p_before, i_cdgb_x001) - p_offset
            p_lw_offset[i_cdgb_x001] = p_offset

        i_cdga = np.union1d(np.union1d(i_cdga_x001, i_cdga_x01), i_cdga_x1)
        i_cdgb = np.union1d(np.union1d(i_cdgb_x001, i_cdgb_x01), i_cdgb_x1)

        if len(i_cdga) > 0:
            e_fill[i_cdga] = self.CDGA.get_error_interpol(p_fill[i_cdga], self.unit)
            e_lw[i_cdga] = self.CDGA.get_error_interpol(p_lw[i_cdga], self.unit)

        if len(i_cdgb) > 0:
            e_fill[i_cdgb] = self.CDGB.get_error_interpol(p_fill[i_cdga], self.unit)
            e_lw[i_cdgb] = self.CDGB.get_error_interpol(p_lw[i_cdgb], self.unit)

        p_fill = p_fill/(e_fill + 1)
        p_lw = p_lw/(e_lw + 1)

        ana.store("Pressure", "fill",  p_fill, self.unit)
        ana.store("Pressure", "fill_offset",  p_fill_offset, self.unit)
        ana.store("Error", "fill",  e_fill, "1")

        ana.store("Pressure", "lw",  p_fill, self.unit)
        ana.store("Pressure", "lw_offset",  p_fill_offset, self.unit)
        ana.store("Error", "lw",  e_fill, "1")
