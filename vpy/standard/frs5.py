import copy
import numpy as np
import sympy as sym

from ..vpy_io import Io
from ..document import Document
from ..standard.standard import Standard
from ..device.srg import Srg
from ..constants import Constants
from ..calibration_devices import  CalibrationObject
from ..values import Temperature, Pressure, Time, AuxFrs5


class Frs5(Standard):
    """Configuration and methodes of large area piston gauge FRS5.
    """

    io = Io()
    log = io.log(__name__)
    log.info("start logging")

    name = "FRS5"
    unit = "mbar"

    def __init__(self, orgdoc):
        super().__init__(orgdoc, self.name)

        doc = copy.deepcopy(orgdoc)
        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxFrs5(doc)

        # constants of standard
        self.A_eff    = self.get_value("A_eff", "m^2")
        self.g        = self.get_value("g_frs", "m/s^2")
        self.r_cal    = self.get_value("R_cal", "lb")
        self.m_cal    = self.get_value("m_cal", "kg")
        self.rho_frs  = self.get_value("rho_frs", "kg/m^3")
        self.rho_gas  = self.get_value("rho_gas", "kg/m^3")
        self.ab       = self.get_value("alpha_beta_frs", "1/C")

        resdev = self.Cobj.get_by_name("FRS55_4019")
        self.ResDev = Srg(doc, resdev)

    def get_name(self):
        """Returns the name of the standard

        :returns: name of standard
        :rtype: str
        """
        return self.name

    def get_gas(self):
        """Returns the name of the calibration gas stored in *AuxValues*

        .. todo::

                implementation of aux.gas needed

        """

        self.log.warn("Default gas N2 used")
        return "N2"

    def uncertainty(self, res):
        """Calculates the total uncertainty.
        sympy derives the sensitivity coefficients.

        * ``p_frs``    ... abs. pressure of the piston gauge [p]=Pa
        * ``r``        ... reading [r] = lb
        * ``u_b``      ... standard uncertainty of the balance [u_b] = lb (4.4e-6+5e-6*R)
        * ``u_sys``    ... sys. uncertanty of the balance [u_sys]=lb (1e-5*R)
        * ``r_0``      ... zero reading [r_0] = lb
        * ``A``        ... effective area [A]= m^2
        * ``p_res``    ... residual pressure [p.res]=Pa
        * ``m_cal``    ... calibration mass piece [m.cal]=kg
        * ``rho_gas``  ... density gas
        * ``rho_frs``  ... density frs piston
        * ``g``        ... accelaration [g]=m/s^2
        * ``r_cal``    ... indication at m_cal [r_cal]=g
        * ``r_cal_0``  ...  indication at zero [r_cal_0]=g
        * ``ab``       ... temperatur coeff. [k]=1/K
        * ``t``        ... temperature of balance [t]=C

        model equation:

        .. math::

            p=\\frac{r_{ind}-r_0+u_b+u_{sys}}{r_{cal}-r_{cal 0}}\\
             m_{cal}\\frac{g}{A_{eff}}\\frac{1}{corr_{rho}corr_{tem}}

        """
        r          = sym.Symbol('r')
        ub         = sym.Symbol('ub')
        usys       = sym.Symbol('usys')
        r_0        = sym.Symbol('r_0')
        A          = sym.Symbol('A')
        p_res      = sym.Symbol('p_res')
        m_cal      = sym.Symbol('m_cal')
        g          = sym.Symbol('g')
        r_cal      = sym.Symbol('r_cal')
        r_cal0    = sym.Symbol('r_cal0')
        ab         = sym.Symbol('ab')
        tem        = sym.Symbol('tem')
        rho_frs    = sym.Symbol('rho_frs')
        rho_gas    = sym.Symbol('rho_gas')

        p_frs = sym.S((r+ub+usys)/(r_cal-r_cal0)
                      *m_cal*g/A/(1-rho_gas/rho_frs)/(1.0+ab*(tem-20.0))) + p_res

        s_r          = sym.diff(p_frs, r)
        s_ub         = sym.diff(p_frs, ub)
        s_usys       = sym.diff(p_frs, usys)
        s_r_cal      = sym.diff(p_frs, r_cal)
        s_r_cal0     = sym.diff(p_frs, r_cal0)
        s_m_cal      = sym.diff(p_frs, m_cal)
        s_g          = sym.diff(p_frs, g)
        s_A          = sym.diff(p_frs, A)
        s_tem        = sym.diff(p_frs, tem)
        s_tem        = sym.diff(p_frs, tem)
        s_rho_gas    = sym.diff(p_frs, rho_gas)
        s_rho_frs    = sym.diff(p_frs, rho_frs)

        u_r       = self.get_expression("u_r", "lb")
        u_A       = self.get_expression("u_A", "m^2")
        u_r_0     = self.get_expression("u_r_0", "lb")
        u_ub      = self.get_expression("u_ub", "lb")
        u_usys    = self.get_expression("u_usys", "lb")
        u_r_cal   = self.get_expression("u_r_cal", "lb")
        u_r_cal0  = self.get_expression("u_r_cal0", "lb")
        u_m_cal   = self.get_expression("u_m_cal", "kg")
        u_rho_frs = self.get_expression("u_rho_frs", "kg/m^3")

        # relative uncertainties
        u_g      = self.get_expression("u_g", "1") * self.g

        # gas dependend
        gas = self.get_gas()
        u_rho_gas  = self.get_expression("u_rho_frs", "kg/m^3")


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

        .. math::

            p=\\frac{r}{r_{cal}} m_{cal}\\frac{g}{A_{eff}}\\
                \\frac{1}{corr_{rho}corr_{tem}} + p_{res}

        with

        .. math::

                corr_{rho} = 1 - \\frac{\\rho_{gas}}{\\rho_{piston}}

        and

        .. math::

                corr_{tem} = 1 + \\alpha \\beta (\\vartheta - 20)
        """
        conv     = self.Cons.get_conv("Pa", "mbar")
        tem      = self.Temp.get_value("frs5", "C")
        mt       = self.Time.get_value("amt_frs5_ind", "ms")
        r_zc0    = self.Aux.get_val_by_time(mt, "offset_mt", "ms", "frs_zc0_p", "lb")
        r_zc     = self.Pres.get_value("frs_zc_p", "lb")
        r_ind    = self.Pres.get_value("frs_p", "lb")

        N        = len(r_ind)

        # correction buoyancy
        corr_rho = (1.0 - self.rho_gas / self.rho_frs)
        corr_rho = np.full(N, corr_rho)
        res.store("Correction", "buoyancy_frs5", corr_rho, "1")

        # correction temperature
        tem      =  res.pick("Temperature", "frs5", "C")
        corr_tem = (1.0 + self.ab * (tem - 20.0))
        res.store("Correction", "temperature_frs5", corr_tem, "1")

        # conversion lb to Pa
        f        = self.m_cal/self.r_cal * self.g/(self.A_eff * corr_rho * corr_tem) # Pa
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
