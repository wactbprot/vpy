import numpy as np
import sympy as sym

from .std import Se3

class Uncert(Se3):

    def __init__(self, doc):
        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def uncert_total(self, res):

        self.gen_val_dict(res)
        self.gen_val_array(res)

    def uncert_p_fill(self, res):
        """ Calculates theuncertainty of the filling pressure_fill.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conf_targ = self.val_conf["Pressure"]["FillTarget"]
        conf_fill = self.val_conf["Pressure"]["Fill"]

        fill_target   = self.Pres.get_value(conf_targ["Type"],
                                            conf_targ["Unit"])

        N   = np.shape(conf_fill)[0]
        M   = self.no_of_meas_points
        u_arr = []

        for i in range(N):
            FillDev = self.FillDevs[i]
            u_arr.append(FillDev.get_total_rel_uncert(fill_target, conf_targ["Unit"]))

        res.store("Uncertainty", "u_V_start", np.absolute(val/p_nom),"1")
        self.log.debug("uncert u_V_start: {}".format(val/p_nom))

        print(np.power(np.nansum(np.power(u_arr, -1), axis=0), -1))

    def uncert_v_start(self, res):
        """Calculates the uncertainty contribution
        of the starting volume

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        f         = self.get_expansion()
        u_V_start = np.full(self.no_of_meas_points, np.nan)

        i_s = np.where(f == "f_s")
        if np.shape(i_s)[1] > 0:
            u_V_start[i_s] = self.get_value("u_V_s","cm^3")

        i_m = np.where(f == "f_m")
        if np.shape(i_m)[1] > 0:
            u_V_start[i_m] = self.get_value("u_V_m","cm^3")

        i_l = np.where(f == "f_l")
        if np.shape(i_l)[1] > 0:
            u_V_start[i_l] = self.get_value("u_V_l","cm^3")

        s_expr = sym.diff(self.model, sym.Symbol('V_start'))
        u      = sym.lambdify(self.symb, s_expr, "numpy")
        val    = u(*self.val_arr)*u_V_start

        p_nom = self.val_dict['f']*self.val_dict['p_fill']

        res.store("Uncertainty", "v_start", np.absolute(val/p_nom),"1")
        self.log.debug("uncert v_start: {}".format(val/p_nom))

    def uncert_v_5(self, res):
        """Calculates the uncertainty contribution
         of the  volume 5

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
            :type: class
            """

        u_V_5 =  np.full(self.no_of_meas_points,self.get_value("u_V_5","cm^3"))
        s_expr = sym.diff(self.model, sym.Symbol('V_5'))
        u      = sym.lambdify(self.symb, s_expr, "numpy")
        val    = u(*self.val_arr)*u_V_5

        p_nom = self.val_dict['f'] * self.val_dict['p_fill']

        res.store("Uncertainty", "v_5", np.absolute(val/p_nom),"1")
        self.log.debug("uncert v_5: {}".format(val/p_nom))
