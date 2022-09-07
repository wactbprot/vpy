import sys
import numpy as np
from .std import Ce3

class Uncert(Ce3):
    pressure_unit = "mbar"
    temperature_unit = "K"
    rel_unit = "1"

    def __init__(self, doc):
        super().__init__(doc)

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

        ana.store("Uncertainty", "fill", u/p_fill, "1")

    def range_index(self, D, x, u):

        conv = self.Cons.get_conv(D.get("RangeUnit"), u)
        i_to = np.where(x < np.float(D.get("To")) * conv)
        i_from = np.where(x > np.float(D.get("From")) * conv)

        return np.intersect1d(i_to, i_from)

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
        u[i] = np.abs(F1[i] * F2 * (1. + 2 * np.log(0.1/p_fill[i])))

        ana.store("Uncertainty", "therm_transp", u/p_fill, "1")
        ## ## Gleichung s. [[QSE-FM3-98_10#Unsicherheiten_durch_Abweichen_des
        ## ## _tats.C3.A4chlichen_Drucks_vom_gemessen_Druck]]

    def delta_V(self, ana):
        p_fill = ana.pick("Pressure", "fill", self.pressure_unit)
        if self.opk == "opK1":
            delta_G = self.get_value("deltaG", "g")
            ua = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_a", "g"))/delta_G
            ub = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_b", "1"))
            uc = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_c", "g"))/delta_G
            ud = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_d", "1"))
            ue = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_e", "1"))
            uf = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_f", "1"))
            ug = np.full(self.no_of_meas_points, self.get_value("fm3DeltaV_u2_g", "1"))

            u = np.sqrt(np.power(ua, 2) +
                        np.power(ub, 2) +
                        np.power(uc, 2) +
                        np.power(ud, 2) +
                        np.power(ue, 2) +
                        np.power(uf, 2) +
                        np.power(ug, 2))
            ana.store("Uncertainty", "delta_V", u, "1")
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
                u1 = self.get_value("fm3DeltaVDeltatLw1_u1", "1")
                u[i_C1] = u1

            if len(i_C2) > 0:

                Ua = self.get_dict("Type", "fm3DeltaVDeltatLw2_u1_a")
                Ub = self.get_dict("Type", "fm3DeltaVDeltatLw2_u1_b")

                ia = self.range_index(Ua, p_fill, self.pressure_unit)
                ib = self.range_index(Ub, p_fill, self.pressure_unit)

                if len(ia) > 0 and len(ib) > 0 and len(ia) == len(ib):
                    ua = np.float(Ua.get("Value"))
                    ub = np.float(Ub.get("Value"))
                    u[ia] = ua * np.log(1/p_fill[ia]) * ub
                else:
                    sys.exit("length problem at uncert function delta_V_delta_t")

            Uc = self.get_dict("Type", "fm3DeltaVDeltatLw2_u1_c")
            ic = self.range_index(Uc, p_fill, self.pressure_unit)
            if len(ic) > 0:
                uc = np.float(Uc.get("Value"))
                u[ic] = uc
            else:
                sys.exit("length problem at uncert function delta_V_delta_t")
            print(u)
        else:
            sys.exit("not implemented")
