import numpy as np
import sympy as sym
from .std import Frs5


class Cal(Frs5):

    def __init__(self, doc):
        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def pressure_res(self, res):
        """Calculates the residual Pressure from
        SRG-DCR values.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        ## untestet methode call:
        tem, tem_unit = self.Temp.get_value_and_unit("frs5")
        gas = self.Aux.get_gas()
        mt = self.Time.get_value("amt_meas", "ms")

        off = self.Aux.get_obj_by_time(
            mt, "offset_mt", "ms", "frs_res_off", "DCR")
        res_off = self.ResDev.pressure(off, tem, "mbar", gas)

        ## untestet methode call:
        ind, ind_unit = self.Pres.get_value_and_unit("frs_res_ind")
        res_ind = self.ResDev.pressure(ind, tem, "mbar", gas)
        p_res = res_ind - res_off

        res.store('Pressure', "frs5_res_off", res_off, "mbar")
        res.store('Pressure', "frs5_res_ind", res_ind, "mbar")
        res.store('Pressure', "frs5_res", p_res, "mbar")

        self.log.debug("residial FRS5 pressure is: {}".format(p_res))

    def temperature(self, res):
        """
        Temperature of the balance.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        tem = self.Temp.get_value("frs5", "C")
        res.store('Temperature', "frs5", tem, "C")

    def pressure_cal(self, res):
        """Calculates the FRS5 calibration pressure from
        lb indication. The equation is:

        .. math::
                p=\\frac{r}{r_{cal}} m_{cal}\\frac{g}{A_{eff}}\\
                \\frac{1}{corr_{rho}corr_{tem}} + p_{res}

        with

        .. math::
                corr_{rho} = 1 - \\frac{\\rho_{gas}}{\\rho_{piston}}

        and

        .. math::
                corr_{tem} = 1 + \\alpha \\beta (\\vartheta - 20)

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        self.temperature(res)
        self.pressure_res(res)
        N = self.no_of_meas_points
        A = self.get_value_full("A_eff", "m^2", N)
        r_cal = self.get_value_full("R_cal", "lb", N)
        m_cal = self.get_value_full("m_cal", "kg", N)
        g = self.get_value_full("g_frs", "m/s^2", N)

        # correction buoyancy  piston
        rho_frs = self.get_value_full("rho_frs", "kg/m^3", N)

            ## Temperature in C
        T = res.pick("Temperature", "frs5", "C")
        ab = self.get_value_full("alpha_beta_frs", "1/C", N)

        # correction buoyancy  get info for gas
        approx_p = self.Pres.get_value("frs_p", "lb") * 10.0  # mbar
        gas = self.get_gas()
        conv_T = self.Cons.get_conv("C", "K")

        rho_gas = self.Cons.get_gas_density(
            gas, approx_p, "mbar", T + conv_T, "K", "kg/m^3")


        # residual pressure in mbar
        p_res = res.pick("Pressure", "frs5_res", self.unit)

        # correction offset drift
        # get measure time for r_zc0
        meas_time = self.Time.get_value("amt_meas", "ms")

        r_zc0 = self.Aux.get_val_by_time(meas_time, "offset_mt", "ms", "frs_zc0_p", "lb")
        r_zc = self.Pres.get_value("frs_zc_p", "lb")

        r_0 = r_zc - r_zc0

        # correction buoyancy
        corr_rho = 1.0 / (1.0 - rho_gas / rho_frs)

        # correction temperature
        corr_temp = 1.0 / (1.0 + ab * (T - 20.0))

        ## lp to Pa
        conv = m_cal / r_cal * g / A * corr_rho * corr_temp
        ## Pa to self.unit
        conv_p = self.Cons.get_conv("Pa", self.unit, N)
        r = self.Pres.get_value("frs_p", "lb")
        p = (r - r_0) * conv * conv_p + p_res

        res.store("Correction", "buoyancy_frs5", corr_rho, "1")
        res.store("Correction", "temperature_frs5", corr_temp, "1")
        res.store('Pressure', "frs5", p, self.unit)
