import copy
import numpy as np

from log import log
from document import Document
from standard.standard import Standard
from device.srg import Srg
from constants import Constants
from calibration_devices import  CalibrationObject
from values import Temperature, Pressure, Time, AuxFrs5


class Frs5(Standard):
    """Configuration and methodes of large area piston gauge FRS5.
    """
    log = log().getLogger(__name__)
    log.info("Document class ini")

    name = "FRS5"
    unit = "mbar"

    def __init__(self, orgdoc):
        super().__init__(orgdoc, self.name)

        doc = copy.deepcopy(orgdoc)

        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxFrs5(doc)

        resdev = self.Cobj.get_by_name("FRS55_4019")
        self.ResDev = Srg(doc, resdev)

    def get_name(self):
        return self.name

    def pressure_res(self, res):
        """Calculates the residual Pressure from
        SRG-DCR values.
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
        tem      = self.Temp.get_value("frs5", "C")
        res.store('Temperature',"frs5", tem , "C")

    def pressure_cal(self, res):
        """Calculates the FRS5 calibration pressure from
        lb indication. The equation is:

        :math:`p=\\frac{r}{r_{cal}} m_{cal}\\frac{g}{A_{eff}}\\frac{1}{corr_{rho}corr_{tem}}`

        with

        :math:`corr_{rho} = 1 - \\frac{\\rho_{gas}}{\\rho_{piston}}`

        and

        :math:`corr_{tem} = 1 + \\alpha \\beta (\\vartheta - 20)`
        """

        A_eff    = self.get_value("A_eff", "m^2")
        g        = self.get_value("g_frs", "m/s^2")
        r_cal    = self.get_value("R_cal", "lb")
        m_cal    = self.get_value("m_cal", "kg")
        rho_frs  = self.get_value("rho_frs", "kg/m^3")
        rho_gas  = self.get_value("rho_gas", "kg/m^3")
        ab       = self.get_value("alpha_beta_frs", "1/C")
        conv     = self.Cons.get_conv("Pa", "mbar")

        tem      = self.Temp.get_value("frs5", "C")
        mt       = self.Time.get_value("amt_frs5_ind", "ms")

        r_zc0    = self.Aux.get_val_by_time(mt, "offset_mt", "ms", "frs_zc0_p", "lb")
        r_zc     = self.Pres.get_value("frs_zc_p", "lb")
        r_ind    = self.Pres.get_value("frs_p", "lb")
        N        = len(r_ind)
        # correction buoyancy
        corr_rho = (1.0 - rho_gas / rho_frs)
        corr_rho = np.full(N, corr_rho)
        res.store("Correction", "buoyancy_frs5", corr_rho, "1")

        # correction temperature
        tem      =  res.pick("Temperature", "frs5", "C")
        corr_tem = (1.0 + ab * (tem - 20.0))
        res.store("Correction", "temperature_frs5", corr_tem, "1")

        # conversion lb to Pa
        f        = m_cal/r_cal * g/(A_eff * corr_rho * corr_tem) # Pa
        # offset
        r_0      = r_zc - r_zc0
        p_0      = r_0 * f * conv
        res.store('Pressure',"frs5_off", p_0 , "mbar")

        # indication
        r        = r_ind - r_0
        p        = r * f * conv
        p_res    = res.pick("Pressure", "frs5_res", "mbar")
        p_corr    = p  + p_res
        res.store('Pressure',"frs5", p_corr , "mbar")
