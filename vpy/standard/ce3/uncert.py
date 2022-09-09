import sys
import numpy as np
from .std import Ce3

class Uncert(Ce3):
    pressure_unit = "mbar"
    temperature_unit = "K"
    rel_unit = "1"

    def __init__(self, doc):
        super().__init__(doc)

    def range_index(self, D, x, u):

        conv = self.Cons.get_conv(D.get("RangeUnit"), u)
        i_to = np.where(x < np.float(D.get("To")) * conv)
        i_from = np.where(x > np.float(D.get("From")) * conv)

        return np.intersect1d(i_to, i_from)

    def pressure_fill(self, ana):
        u = np.full(self.no_of_meas_points, np.nan)
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)

        u_cdga = self.CDGA.get_total_uncert(p_fill, self.pressure_unit, self.pressure_unit)
        u_cdgb = self.CDGB.get_total_uncert(p_fill, self.pressure_unit, self.pressure_unit)

        for i, _ in enumerate(p_fill):
            if np.isnan(u_cdga[i]):
                u[i] = u_cdgb[i]
            else:
                u[i] = u_cdga[i]

        ana.store("Uncertainty", "pressure_fill", u/p_fill, self.rel_unit)

    def pressure_therm_transp(self, ana):

        ## Drücke die nicht in Bereich fallen,
        ## haben diese Unsicherheit nicht
        ## d.h. der result vektor kann mit 0en initialisiert werden:
        u = np.full(self.no_of_meas_points, 0.0)
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)
        t_fm = ana.pick("Temperature", "fm", self.temperature_unit)
        t_pbox = ana.pick("Temperature", "pbox", self.temperature_unit)

        U = self.get_dict("Type", "fm3ThermTrans_u1")

        i = self.range_index(U, p_fill, self.pressure_unit)

        F1 = np.abs(1. - np.sqrt(t_fm/t_pbox))
        F2 = np.float(U.get("Value"))
        u[i] = np.abs(F1[i] * F2 * (1. + 2. * np.log(0.1/p_fill[i])))

        ana.store("Uncertainty", "pressure_therm_transp", u/p_fill, self.rel_unit)
        ## ## Gleichung s. [[QSE-FM3-98_10#Unsicherheiten_durch_Abweichen_des
        ## ## _tats.C3.A4chlichen_Drucks_vom_gemessen_Druck]]

    def delta_V(self, ana):
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)
        if self.opk == "opK1":
            delta_G = self.get_value("deltaG", "g")
            ua = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_a", "g"))/delta_G
            ub = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_b", self.rel_unit))
            uc = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_c", "g"))/delta_G
            ud = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_d", self.rel_unit))
            ue = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_e", self.rel_unit))
            uf = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_f", self.rel_unit))
            ug = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_g", self.rel_unit))

            u = np.sqrt(np.power(ua, 2) +
                        np.power(ub, 2) +
                        np.power(uc, 2) +
                        np.power(ud, 2) +
                        np.power(ue, 2) +
                        np.power(uf, 2) +
                        np.power(ug, 2))

            ana.store("Uncertainty", "delta_V", u, self.rel_unit)
        else:
            sys.exit("not implemented")

    def delta_V_delta_t(self, ana):
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)
        C_name = np.array(ana.pick_dict("Conductance", "name").get("Value"))
        u = np.full(self.no_of_meas_points, np.nan)
        i_C1 = np.where(C_name == self.name_C1)
        i_C2 = np.where(C_name == self.name_C2)

        if self.opk == "opK1":

            if len(i_C1) > 0:
                u1 = self.get_value("fm3DeltaVDeltatLw1_u1", self.rel_unit)
                u[i_C1] = u1

            if len(i_C2) > 0:

                Ua = self.get_dict("Type", "fm3DeltaVDeltatLw2_u1_a")
                Ub = self.get_dict("Type", "fm3DeltaVDeltatLw2_u1_b")

                ia = self.range_index(Ua, p_fill, self.pressure_unit)
                ib = self.range_index(Ub, p_fill, self.pressure_unit)

                if len(ia) > 0 and len(ib) > 0 and len(ia) == len(ib):
                    i = np.intersect1d(ia, i_C2)

                    ua = np.float(Ua.get("Value"))
                    ub = np.float(Ub.get("Value"))
                    u[i] = ua + ub * np.log(1/p_fill[i])
                else:
                    sys.exit("length problem at uncert function delta_V_delta_t")

                Uc = self.get_dict("Type", "fm3DeltaVDeltatLw2_u1_c")
                ic = self.range_index(Uc, p_fill, self.pressure_unit)
                i = np.intersect1d(ic, i_C2)
                if len(i) > 0:
                    uc = np.float(Uc.get("Value"))
                    u[i] = uc
                else:
                    sys.exit("length problem at uncert function delta_V_delta_t")

            ana.store("Uncertainty", "delta_V_delta_t", u, self.rel_unit)

        else:
            sys.exit("not implemented")

    def delta_t(self, ana):
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)
        C_name = np.array(ana.pick_dict("Conductance", "name").get("Value"))
        u = np.full(self.no_of_meas_points, np.nan)
        i_C1 = np.where(C_name == self.name_C1)
        i_C2 = np.where(C_name == self.name_C2)

        if self.opk == "opK1":
            u1 = self.get_value("fm3Deltat_u1", self.rel_unit)
            if len(i_C1) > 0:

                u2 = self.get_value("fm3Deltat_u2", self.rel_unit)

                u3a = self.get_value("fm3DeltatLw1_u3_a", self.rel_unit)
                u3b = self.get_value("fm3DeltatLw1_u3_b", self.rel_unit)
                u[i_C1] = np.sqrt(np.power(u3a + u3b * np.log(p_fill[i_C1]), 2) + np.power(u1, 2) + np.power(u2, 2))
            if len(i_C2) > 0:
                u3 = self.get_value("fm3DeltatLw2_u3", self.rel_unit)
                u[i_C2] = np.sqrt(np.power(u1, 2) + np.power(u2, 2) + np.power(u3, 2))

            ana.store("Uncertainty", "delta_t", u, self.rel_unit)

        else:
            sys.exit("not implemented")

    def pressure_res(self, ana):
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)
        u = np.full(self.no_of_meas_points, self.get_value("fm3Pres_u1",self.pressure_unit )/p_fill)

        ana.store("Uncertainty", "pressure_res", u, self.rel_unit)

    def flow_pV(self, ana):
        u1 = ana.pick("Uncertainty", "pressure_fill", self.rel_unit)
        u2 = ana.pick("Uncertainty", "pressure_therm_transp", self.rel_unit)
        u3 = ana.pick("Uncertainty", "delta_V", self.rel_unit)
        u4 = ana.pick("Uncertainty", "delta_t", self.rel_unit)
        u5 = ana.pick("Uncertainty", "delta_V_delta_t", self.rel_unit)
        u6 = ana.pick("Uncertainty", "pressure_res", self.rel_unit)

        u = np.sqrt(np.power(u1, 2) +
                    np.power(u2, 2) +
                    np.power(u3, 2) +
                    np.power(u4, 2) +
                    np.power(u5, 2) +
                    np.power(u6, 2))
        u = np.full(self.no_of_meas_points, u)

        ana.store("Uncertainty", "flow_pV", u, self.rel_unit)

    def conductance(self, ana):
        p_cal = ana.pick("Pressure", "cal", self.pressure_unit)

        if self.opk == "opK1":
            ua = self.get_value("ce3C1_u1_a", self.rel_unit)
            ub = self.get_value("ce3C1_u1_b", "1/mbar")
            u = np.sqrt(np.power(ua, 2) +
                        np.power(ub * p_cal, 2))
        else:
            sys.exit("not implemented")

        u = np.full(self.no_of_meas_points, u)

        ana.store("Uncertainty", "conductance_Cx", u, self.rel_unit)

    def flow_split(self, ana):
        if self.opk == "opK1":
            u = self.get_value("ce3qsplit_u1_a", self.rel_unit)
        else:
            sys.exit("not implemented")

        u = np.full(self.no_of_meas_points, u)

        ana.store("Uncertainty", "flow_split", u, self.rel_unit)

    def temperature_fm(self, ana):
        t_fm = ana.pick("Temperature", "fm", self.temperature_unit)
        u_dev = self.TDev.get_total_uncert(t_fm, self.temperature_unit, self.temperature_unit)/t_fm
        u1 = self.get_value("fm3Tfm_u1", "K")/t_fm
        u2 = self.get_value("fm3Tfm_u2", "K")/t_fm
        u3 = self.get_value("fm3Tfm_u3", "K")/t_fm

        u = np.sqrt(np.power(u_dev, 2) +
                    np.power(u1, 2) +
                    np.power(u2, 2) +
                    np.power(u3, 2))

        ana.store("Uncertainty", "temperature_fm", u, self.rel_unit)


    def temperature_uhv(self, ana):
        t_uhv = ana.pick("Temperature", "uhv", self.temperature_unit)
        u_dev = self.TDev.get_total_uncert(t_uhv, self.temperature_unit, self.temperature_unit)/t_uhv
        u1 = self.get_value("ce3Tch_u1", "K")/t_uhv
        u2 = self.get_value("ce3Tch_u2", "K")/t_uhv

        u = np.sqrt(np.power(u_dev, 2) +
                    np.power(u1, 2) +
                    np.power(u2, 2))

        ana.store("Uncertainty", "temperature_uhv", u, self.rel_unit)

    def pressure_corr(self, ana):
        u = np.full(self.no_of_meas_points, self.get_value("ce3F_u1", self.rel_unit))

        ana.store("Uncertainty", "pressure_corr", u, self.rel_unit)

    def total(self, ana):
        u1 = ana.pick("Uncertainty", "flow_pV", self.rel_unit)
        u2 = ana.pick("Uncertainty", "flow_split", self.rel_unit)
        u3 = ana.pick("Uncertainty", "pressure_corr", self.rel_unit)
        u4 = ana.pick("Uncertainty", "temperature_fm", self.rel_unit)
        u5 = ana.pick("Uncertainty", "temperature_uhv", self.rel_unit)
        u6 = ana.pick("Uncertainty", "conductance_Cx", self.rel_unit)

        u = np.sqrt(np.power(u1, 2) +
                    np.power(u2, 2) +
                    np.power(u3, 2) +
                    np.power(u4, 2) +
                    np.power(u5, 2) +
                    np.power(u6, 2))
        u = np.full(self.no_of_meas_points, u)

        ana.store("Uncertainty", "standard", u, self.rel_unit)
