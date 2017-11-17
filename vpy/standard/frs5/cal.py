import numpy as np
import sympy as sym


from .std import Frs5
from ...vpy_io import Io

class Cal(Frs5):

    def __init__(self, doc):
        super().__init__(doc)

        self.log = Io().logger(__name__)


    def pressure_res(self, res):
        """Calculates the residual Pressure from
        SRG-DCR values.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        tem = self.Temp.get_obj("frs5", "C")
        gas = self.Aux.get_gas()
        mt  = self.Time.get_value("amt_frs5_ind", "ms")

        off = self.Aux.get_obj_by_time(mt, "offset_mt", "ms", "frs_res_off", "DCR")
        res_off = self.ResDev.pressure(off, tem, "mbar", gas)

        ind     = self.Pres.get_obj("frs_res_ind", "DCR")
        res_ind = self.ResDev.pressure(ind, tem, "mbar", gas)

        res.store('Pressure',"frs5_res_off", res_off, "mbar")
        res.store('Pressure',"frs5_res_ind", res_ind, "mbar")
        res.store('Pressure',"frs5_res", res_ind - res_off , "mbar")

    def temperature(self, res):
        """
        Temperature of the balance.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        tem      = self.Temp.get_value("frs5", "C")
        res.store('Temperature',"frs5", tem , "C")


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

        # constants of standard
        A        = self.get_value("A_eff","m^2")
        g        = self.get_value("g_frs","m/s^2")
        r_cal    = self.get_value("R_cal","lb")
        m_cal    = self.get_value("m_cal","kg")
        rho_frs  = self.get_value("rho_frs", "kg/m^3")
        rho_gas  = self.get_value("rho_gas","kg/m^3")
        ab       = self.get_value("alpha_beta_frs", "1/C")
        r        = self.Pres.get_value("frs_p", "lb")
        tem      = res.pick("Temperature", "frs5", "C")
        p_res    = res.pick("Pressure", "frs5_res", self.unit)

        # correction buoyancy
        corr_rho = (1.0-rho_gas/rho_frs)
        corr_rho = np.full(self.no_of_meas_points, corr_rho)

        # correction temperature
        corr_tem = (1.0 + ab * (tem - 20.0))

        # conversion Pa  to unit
        conv     = self.Cons.get_conv("Pa", self.unit)

        # conversion lb to Pa
        f = m_cal/r_cal*g/(A*corr_rho * corr_tem) # Pa

        # offset reading
        mt    = self.Time.get_value("amt_frs5_ind", "ms")
        r_zc0 = self.Aux.get_val_by_time(mt, "offset_mt", "ms", "frs_zc0_p", "lb")
        r_zc  = self.Pres.get_value("frs_zc_p", "lb")
        r_0   = r_zc-r_zc0

        # offset pressure
        p_0 = r_0*f*conv
        # indication
        p_corr   = r*f*conv - p_0 + p_res

        res.store("Correction", "buoyancy_frs5", corr_rho, "1")
        res.store("Correction", "temperature_frs5", corr_tem, "1")
        res.store('Pressure', "frs5_off", p_0, self.unit)
        res.store('Pressure', "frs5", p_corr, self.unit)
