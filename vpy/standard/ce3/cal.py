import numpy as np
import copy
import sympy as sym
from .std import Ce3
from ...values import Values as Val

class Cal(Ce3):
    np.warnings.filterwarnings('ignore')
    R_sz_min = 0.9 ## Grenze Korrelation SZ

    def __init__(self, doc):
        super().__init__(doc)

    def V_fit(self, h):

        ## 	fn.Afit <- function(sl, prefix, sufix, x){
        ## 	    fname  <- deparse(match.call()[[1]])
        ##
        ## 	    A      <- getConstVal(sl, paste0(prefix, "A", sufix))
        ## 	    B      <- getConstVal(sl, paste0(prefix, "B", sufix))
        ## 	    C      <- getConstVal(sl, paste0(prefix, "C", sufix))
        ##
        ## 	    if(length(A) > 0 & length(B) > 0 & length(C) > 0){
        ## 	        return(A*x^3/3 + A * B * x^2 + x*(A * B^2 + C))
        ## 	    }else{
        ## 	        stop(paste("no params found in function:", fname))
        ## 	    }
        ## 	}
        A = self.get_value("fbv_A", "1")
        B = self.get_value("fbv_B", "mm")
        C = self.get_value("fbv_C", "mm^2")

        return A * np.power(h, 3) / 3 + A * B * np.power(h, 2) + h * (A * np.power(B, 2) + C)

    def drift(self, ana):
        slope_drift_before = self.Drift.get_value("drift_before_slope_x", "mbar/ms")
        slope_drift_after = self.Drift.get_value("drift_after_slope_x", "mbar/ms")
        slope_drift = (slope_drift_before + slope_drift_after) / 2

        ana.store("Drift", "drift_slope", slope_drift, "mbar/ms")

    def delta_t(self, SZ):
        ## delta t
        slope_x =  SZ.get_value("slope_x", "mbar/ms")
        t_mean = SZ.get_value("mean_t", "ms")
        p_mean = SZ.get_value("mean_p", "mbar")
        t_mean = t_mean - np.min(t_mean)

        ci = p_mean - slope_x * t_mean
        t_zero = (np.mean(p_mean) -ci) / slope_x
        dt = np.diff(t_zero) * self.Cons.get_conv("ms", "s")
        sd =  np.nanmean(np.nanstd(dt) / np.nanmean(dt))/np.sqrt(len(dt))

        return dt, sd

    def delta_V(self, SZ):
        ## delta V
        ds = SZ.get_value("turn", "turn")
        h = np.abs(ds * self.get_value("turn_2_mm", "mm/turn"))
        nv = len(h)

        i1 = range(1, nv - 1)
        i2 = range(2, nv)

        dV = (self.V_fit(h[i2]) - self.V_fit(h[i1])) * self.Cons.get_conv("mm^3", "l")
        sd = np.nanmean(np.nanstd(dV) / np.nanmean(dV))/np.sqrt(len(dV))

        return dV, sd

    def conductance_name(self, ana):
        use_L1 = self.get_dict("Type", "useLw1") # gr. LW
        use_L2 = self.get_dict("Type", "useLw2") # kl. LW
        print(np.float(use_L1.get("From")))
        print(np.float(use_L2.get("From")))


    def conductance(self, ana):
        t_start = self.Time.get_str("start_sz_mt")
        slope_drift = ana.pick("Drift", "drift_slope", "mbar/ms")

        C = np.full(self.no_of_meas_points, np.nan)
        C_corr = np.full(self.no_of_meas_points, np.nan)
        sd_C = np.full(self.no_of_meas_points, np.nan)
        drift_corr = np.full(self.no_of_meas_points, np.nan)

        for i, ts in enumerate(t_start):
            SZ = Val(self.Aux.doc.get("C_{}".format(ts)))

            # R = SZ.get_value("R", "1")

            delta_t, sd_delta_t = self.delta_t(SZ)
            delta_V, sd_delta_V = self.delta_V(SZ)

            C[i] =  np.nanmean(delta_V / delta_t)
            sd_C[i] = np.sqrt(np.power(sd_delta_V, 2) + np.power(sd_delta_V, 2))

            slope_x =  SZ.get_value("slope_x", "mbar/ms")
            drift_corr[i] = (1 - slope_drift[i] / np.nanmean(slope_x))
            C_corr[i] = C[i] * drift_corr[i]

        ana.store("Conductance", "cnom", C_corr, "l/s")
        ana.store("Conductance", "cnom_uncorr", C, "l/s")
        ana.store("Conductance", "drift_corr",  drift_corr, "1")
        ana.store("Conductance", "sd_cnom", sd_C, "1")

    def conductance_extrap(self, ana):

        if self.opk == "opK1" or opk == "opK2" or opk == "opK3":
            p_before = ana.pick("Pressure", "lw", "mbar")
            p_after  = ana.pick("Pressure", "fill", "mbar")
            c_before = ana.pick("Conductance", "cnom", "l/s")


    def pressure_dp(self, ana):
        dp_before = self.Pres.get_value("dp_before", self.unit)
        dp_after = self.Pres.get_value("dp_after", self.unit)

        ana.store("Pressure", "db", dp_after - dp_before, self.unit)


    def pressure_fill(self, ana):
        p_fill = np.full(self.no_of_meas_points, np.nan)
        e_fill = np.full(self.no_of_meas_points, np.nan)
        p_fill_offset = np.full(self.no_of_meas_points, np.nan)

        p_lw = np.full(self.no_of_meas_points, np.nan)
        e_lw = np.full(self.no_of_meas_points, np.nan)
        p_lw_offset = np.full(self.no_of_meas_points, np.nan)

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
            e_fill[i_cdgb] = self.CDGB.get_error_interpol(p_fill[i_cdgb], self.unit)
            e_lw[i_cdgb] = self.CDGB.get_error_interpol(p_lw[i_cdgb], self.unit)

        p_fill = p_fill/(e_fill + 1)
        p_lw = p_lw/(e_lw + 1)

        ana.store("Pressure", "fill",  p_fill, self.unit)
        ana.store("Pressure", "fill_offset",  p_fill_offset, self.unit)
        ana.store("Error", "fill",  e_fill, "1")

        ana.store("Pressure", "lw",  p_fill, self.unit)
        ana.store("Pressure", "lw_offset",  p_fill_offset, self.unit)
        ana.store("Error", "lw",  e_fill, "1")
