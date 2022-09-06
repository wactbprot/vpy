import sys
import numpy as np
import copy
import sympy as sym
from .std import Ce3
from ...values import Values as Val

class Cal(Ce3):
    np.warnings.filterwarnings('ignore')
    R_sz_min = 0.9 ## Grenze Korrelation SZ
    name_C1 = "C1" ## gr. LW
    name_C2 = "C2" ## kl. LW
    unit = "mbar"

    def __init__(self, doc):
        super().__init__(doc)

    def pressure_cal(self, ana):
        t_ref = self.Cons.get_value("referenceTemperature", "K")
        R = self.Cons.get_value("R", "Pa m^3/mol/K")
        M = self.Cons.get_value("molWeight_{}".format(self.gas), "kg/mol")
        K4 = self.get_value("K4{}".format(self.port), "1")
        aK2 = self.get_value("aK2", "1")

        mean_free_path = ana.pick("Length", "meanFreePath", "m")
        q_pV =  ana.pick("Flow", "pV", "mbarl/s")

        if self.opk == "opK1":
            r1 = self.get_value("r1", "m")
            K2 = (1. + aK2 * (2. * r1 / mean_free_path))

            K3 = self.get_value("K3Uhv", "1")
            t = ana.pick("Temperature", "uhv", "K")

            A = np.power(r1, 2) * np.pi ## in m^2
            ## c in m/s
            c = np.sqrt(8 * R * t /(np.pi * M))
            ## leitwerte in m^3/s
            C = c/4 * A * K2 * K3
            ##  [qpV] = mbar l/s [C1] = m^3/s
            p_cal =  q_pV/C * K4 * self.Cons.get_conv("Pa", self.unit) * self.Cons.get_conv("mbarl/s", "Pam^3/s")

            ana.store("Pressure", "cal", p_cal, self.unit)

        else:
            sys.exit("not implemented")


    def mean_free_path(self, ana):
        kb = self.Cons.get_value("Kb","J/K")
        u = self.Cons.get_value("u","kg")
        Mr = self.Cons.get_value("molWeight_{}".format(self.gas), "kg/mol")*1000
        visc = self.Cons.get_value("visc_{}".format(self.gas), "Pa s")

        if self.opk == "opK1":
            T = ana.pick("Temperature", "uhv", "K")
            C_nom = self.get_value("nomC1", "m^3/s")
        else:
            sys.exit("not implemented")

        q_pV = ana.pick("Flow", "pV", "mbarl/s")
        p = q_pV/C_nom * self.Cons.get_conv("mbarl/s", "Pam^3/s")

        ## [s] = m
        s = np.sqrt(np.pi) * visc/(2 * p) * np.sqrt(2 * kb * T / (Mr*u))

        ana.store("Length", "meanFreePath", s, "m")

    def extrap_fit(self, x, a, b, c, d):
        return a + b * x + c * np.log(x) + d * np.exp(-x)

    def extrap_fit_C1(self, x):
        ##     fn.2162 <- function(sl, prefix, sufix, x){
        ## fname <- deparse(match.call()[[1]])
        ##         a  <- getConstVal(sl, paste0(prefix, "A", sufix))
        ##         b  <- getConstVal(sl, paste0(prefix, "B", sufix))
        ##         c  <- getConstVal(sl, paste0(prefix, "C", sufix))
        ##         d  <- getConstVal(sl, paste0(prefix, "D", sufix))
        ## if(length(a) > 0 &
        ##    length(b) > 0 &
        ##    length(c) > 0 &
        ##    length(d) > 0){
        ##
        ##     return(raw.2162(x, a, b, c, d))
        ##    }else{
        ##        stop(paste("no params found in function:",fname))
        ##    }
        ## }
        ## raw.2162(x, a, b, c, d))
        ##
        ## return(a + b * x + c * log(x) + d *exp(-x))
        A = self.get_value("grLw_N2_A", "l/s")
        B = self.get_value("grLw_N2_B", "1")
        C = self.get_value("grLw_N2_C", "1")
        D = self.get_value("grLw_N2_D", "1")

        return self.extrap_fit(x, A, B, C, D)

    def extrap_fit_C2(self, x):
        A = self.get_value("klLw_N2_A", "l/s")
        B = self.get_value("klLw_N2_B", "1")
        C = self.get_value("klLw_N2_C", "1")
        D = self.get_value("klLw_N2_D", "1")

        return self.extrap_fit(x, A, B, C, D)

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

    def flow(self, ana):
        R = self.Cons.get_value("R","Pa m^3/mol/K") * self.Cons.get_conv("Pam^3/mol/K", "mbarl/mol/K")
        p_fill = ana.pick("Pressure", "fill", self.unit)
        t_uhv = ana.pick("Temperature", "uhv", "K")
        t_xhv = ana.pick("Temperature", "xhv", "K")
        t_fm = ana.pick("Temperature", "fm", "K")
        C_fm = ana.pick("Conductance", "fm", "l/s")

        if self.opk == "opK1":
            ## KP1 in Betrieb, XHV-TMP-Ventil offen
            ## Messung an uhv- Seite
            A = self.get_value("qSplitCorrUhvOpk1A", "1")
            B = self.get_value("qSplitCorrUhvOpk1B", "1/(mbar l/s)")
            C = self.get_value("qSplitCorrUhvOpk1C", "1/(mbar l/s)^2")


        q_mol = C_fm * p_fill / (R * t_fm)
        ## q.pV.fd wird nur zur Bestimmung des
        ## Flussteilungsfaktors bestimmt
        q_pV_fd =  q_mol * (t_xhv + t_uhv)/2 * R
        ## Faktor Flussaufteilung
        fd_corr = A + B * q_pV_fd + C * np.power(q_pV_fd, 2)
        ## q.pV in mbarl/s
        q_pV_corr = q_mol * t_uhv * R * fd_corr

        ana.store("Flow", "mol", q_mol, "mol/s")
        ana.store("Flow", "pV", q_pV_corr, "mbarl/s")

    def temperature_room(self, ana):
        C_2_K = self.Cons.get_conv("C", "K")
        k_110 = self.TDev.get_value("agilentCorrCh110", "K")
        t_110 = self.Temp.get_value("agilentCh110_after_lw", "C")

        ana.store("Temperature", "room", t_110 + k_110 + C_2_K , "K")

    def temperature_xhv(self, ana):
        C_2_K = self.Cons.get_conv("C", "K")
        k_108 = self.TDev.get_value("agilentCorrCh108", "K")
        t_108b = self.Temp.get_value("agilentCh108_before_lw", "C")
        t_108a = self.Temp.get_value("agilentCh108_after_lw", "C")
        k_109 = self.TDev.get_value("agilentCorrCh109", "K")
        t_109b = self.Temp.get_value("agilentCh109_before_lw", "C")
        t_109a = self.Temp.get_value("agilentCh109_after_lw", "C")

        t = (t_108a + k_108 + t_108b + k_108 +
             t_109a + k_109 + t_109b + k_109) / 4 + C_2_K

        ana.store("Temperature", "xhv", t, "K")

    def temperature_uhv(self, ana):
        C_2_K = self.Cons.get_conv("C", "K")
        k_104 = self.TDev.get_value("agilentCorrCh104", "K")
        t_104b = self.Temp.get_value("agilentCh104_before_lw", "C")
        t_104a = self.Temp.get_value("agilentCh104_after_lw", "C")

        k_105 = self.TDev.get_value("agilentCorrCh105", "K")
        t_105b = self.Temp.get_value("agilentCh105_before_lw", "C")
        t_105a = self.Temp.get_value("agilentCh105_after_lw", "C")

        k_106 = self.TDev.get_value("agilentCorrCh106", "K")
        t_106b = self.Temp.get_value("agilentCh106_before_lw", "C")
        t_106a = self.Temp.get_value("agilentCh106_after_lw", "C")

        k_107 = self.TDev.get_value("agilentCorrCh107", "K")
        t_107b = self.Temp.get_value("agilentCh107_before_lw", "C")
        t_107a = self.Temp.get_value("agilentCh107_after_lw", "C")

        t = (t_104a + k_104 + t_104b + k_104 +
             t_105a + k_105 + t_105b + k_105 +
             t_106a + k_106 + t_106b + k_106 +
             t_107a + k_107 + t_107b + k_107) / 8 + C_2_K

        ana.store("Temperature", "uhv", t, "K")

    def temperature_pbox(self, ana):
        C_2_K = self.Cons.get_conv("C", "K")
        k_103 = self.TDev.get_value("agilentCorrCh103", "K")
        t_103 = self.Temp.get_value("agilentCh103_after_lw", "C")

        ana.store("Temperature", "pbox", t_103 + k_103 + C_2_K , "K")

    def temperature_fm(self, ana):
        C_2_K = self.Cons.get_conv("C", "K")
        k_101 = self.TDev.get_value("agilentCorrCh101", "K")
        t_101 = self.Temp.get_value("agilentCh101_after_lw", "C")
        k_102 = self.TDev.get_value("agilentCorrCh102", "K")
        t_102 = self.Temp.get_value("agilentCh102_after_lw", "C")

        ana.store("Temperature", "fm", (t_101 + k_101 + t_102 + k_102) / 2 + C_2_K , "K")

    def drift(self, ana):
        slope_drift_before = self.Drift.get_value("drift_before_slope_x", "mbar/ms")
        slope_drift_after = self.Drift.get_value("drift_after_slope_x", "mbar/ms")
        slope_drift = (slope_drift_before + slope_drift_after) / 2

        ana.store("Drift", "drift_slope", slope_drift, "mbar/ms")

    def delta_t(self, SZ):
        ## delta t
        slope_x =  SZ.get_value("slope_x", "mbar/ms")
        t_mean = SZ.get_value("mean_t", "ms")
        p_mean = SZ.get_value("mean_p", self.unit)
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
        C_name = np.full(self.no_of_meas_points, "Cx")

        use_C1 = self.get_dict("Type", "useLw1") # gr. LW
        use_C2 = self.get_dict("Type", "useLw2") # kl. LW

        unit_C1 = use_C1.get("RangeUnit")
        unit_C2 = use_C2.get("RangeUnit")
        if unit_C1 == unit_C2:
            unit_C = unit_C1
        else:
            sys.exit("range units don't match")

        from_C1 = np.float(use_C1.get("From"))
        from_C2 = np.float(use_C2.get("From"))

        to_C1 = np.float(use_C1.get("To"))
        to_C2 = np.float(use_C2.get("To"))

        C = ana.pick("Conductance", "cnom", unit_C)
        for i, c in enumerate(C):
            if from_C1 < c < to_C1:
                C_name[i] = self.name_C1
            if from_C2 < c < to_C2:
                C_name[i] = self.name_C2

        ana.store("Conductance", "name", C_name, "")


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

        C_extrap = np.full(self.no_of_meas_points, np.nan)
        C_name = np.array(ana.pick_dict("Conductance", "name").get("Value"))

        i_C1 = np.where(C_name == self.name_C1)
        i_C2 = np.where(C_name == self.name_C2)

        if self.opk == "opK1" or opk == "opK2" or opk == "opK3":
            p_before = ana.pick("Pressure", "lw", self.unit)
            p_after  = ana.pick("Pressure", "fill", self.unit)
            C_before = ana.pick("Conductance", "cnom", "l/s")

        if np.shape(i_C1)[1] > 0:
            C_extrap[i_C1] = C_before[i_C1] * self.extrap_fit_C1(p_after[i_C1]) / self.extrap_fit_C1(p_before[i_C1])

        if np.shape(i_C2)[1] > 0:
            C_extrap[i_C2] = C_before[i_C2] * self.extrap_fit_C2(p_after[i_C2]) / self.extrap_fit_C2(p_before[i_C2])

        diff_nom = C_extrap/C_before - 1

        ana.store("Conductance", "fm", C_extrap, "l/s")
        ana.store("Conductance", "diff_nom", diff_nom, "1")

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

        ana.store("Pressure", "lw",  p_lw, self.unit)
        ana.store("Pressure", "lw_offset",  p_lw_offset, self.unit)
        ana.store("Error", "lw",  e_lw, "1")
