import copy
import numpy as np
import sympy as sym

from ..log import log
from ..document import Document
from ..standard.standard import Standard
from ..device.srg import Srg
from ..constants import Constants
from ..calibration_devices import  CalibrationObject
from ..values import Temperature, Pressure, Time, AuxFrs5


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

    def uncertainty(self, res):
        """Calculates the total uncertainty.
        sympy derives the sensitivity coefficients.

        * p_frs      ... abs. pressure of the piston gauge [p]=Pa
        * r_ind      ... reading [r_ind] = lb
        * u_b        ... standard uncertainty of the balance [u_b] = lb (4.4e-6+5e-6*R)
        * u_sys      ... sys. uncertanty of the balance [u_sys]=lb (1e-5*R)
        * r_0        ... zero reading [r_0] = lb
        * f          ... conversion factor lb-->g [f] = g/lb
        * A          ... effective area [A]= m^2
        * p_res      ... residual pressure [p.res]=Pa
        * m_cal      ... calibration mass piece [m.cal]=kg
        * rho_gas    ... density gas
        * rho_piston ... density piston
        * g          ... accelaration [g]=m/s^2
        * r_cal      ... indication at m_cal [r_cal]=g
        * r_cal_0    ...  indication at zero [r_cal_0]=g
        * ab         ... temperatur coeff. [k]=1/K
        * t          ... temperature of balance [t]=C

        model equation:

        :math:`p=\\frac{r_{ind}-r_0+u_b+u_{sys}}{r_{cal}-r_{cal 0}} m_{cal}\\frac{g}{A_{eff}}\\frac{1}{corr_{rho}corr_{tem}}`

        {
                "Type": "u_r",
                "Value": "8.66e-6",
                "Unit": "lb",
                "Comment": "aus 1. Bericht zur FRS5"
              },
              {
                "Type": "u_ub",
                "Expression": "0.002/453.59+5.0e-6*r_ind",
                "Unit": "lb",
                "Comment": "aus 1. Bericht zur FRS5"
              },
              {
                "Type": "u_usys",
                "Expression": "1.0e-5*r_ind",
                "Unit": "lb",
                "Comment": "aus 1. Bericht zur FRS5"
              },
              {
                "Type": "u_r_0",
                "Value": "2.0e-5",
                "Unit": "lb",
                "Comment": "sind die beobachteten 2e-4mbar Temperaturdrift, Streuung, nichterfassbare Nullpkt.str."
              },
              {
                "Type": "u_A",
                "Value": "1.05e-7",
                "Unit": "m^2",
                "Comment": "(k=1) aus Kalibschein 0187PTB05"
              },
              {
                "Type": "u_p_res_N2",
                "Expression": "7.2e-2*p_res",
                "Unit": "Pa",
                "Comment": "aus Kalib.-schein QS 05/05"
              },
              {
                "Type": "u_p_res_He",
                "Expression": "7.043e-13*(pcal)^3+6.976e-10*(pcal)^2+3.0e-5*(pcal)+6.579e-4",
                "Unit": "Pa",
                "Comment": "Schätzwert aus Messungen f. Dr. Fellmuth JAN07 für He"
              },

               {
                "Type": "u_m_cal",
                "Value": "2.e-6",
                "Unit": "kg",
                "Comment": "aus Kalib.-schein QS 05/05"
              },
              {
                "Type": "u_rho_piston",
                "Value": "50.",
                "Unit": "kg/m^3",
                "Comment": "aus Kalib.-schein QS 05/05"
              },{
                "Type": "u_rho_gas",
                "Expression": "M/T/R*p_frs/2.",
                "Unit": "kg/m^3",
                "Comment": "Abschätzung: Hälfte der Dichte des gemessenen Drucks"
              },

              R      : pcal/sR; /*Eing. pcal in Pa */
              ub    : 0.0;
              usys  : 0.0;

              R0    : 0.000020; /*typischer Wert in lb*/
              A      : 45.3467e-4; /*m^2 aus Kalib.-schein 0187 PTB 05 */
              pres  : 1.5e-3*R; /*Sch�tzwert aus DKM-FRS Vergleichsdaten (Pa)
                                  6.9.06: liefert aber bei 11kPa nur 2e-6mbar!
                                  sollte aber 1e-4mbar sein!!!
                                  11.9.06 korrigiert:
                                  @11kPa   --> 2e-4mbar
                                  @0.03kPa --> 5e-7mbar
                                  ok*/
              mcal  : 1.038867;
              b      : 1.0;
              g      : 9.812718;
              Rcal  : 2.290311;
              R0cal: 0.0;
              k      : 4.0e-6;
              t      : 27.0;


              uR : 8.66e-6; /* aus Bericht in lb*/
              uub :0.002/453.59+5.0e-6*R; /* aus Bericht in lb */
              uusys : 1.0e-5*R;/* aus Bericht in lb */
              uR0 : 2.0e-5; /*sind die beobachteten 2e-4mbar
                             Temperaturdrift, Streuung, nichterfassbare Nullpkt.str.  i
                             n lb*/
              uA : 2.1e-7/2.0; /*m^2 (k=1) aus Kalibschein 0187PTB05*/
              upres : 7.2e-2*pres;/*Pa aus Kalib.-schein QS 05/05*/
              umcal :  2.e-6;/*kg*/
              ub : 0.0;
              ug :1.0e-7;/* TU Angabe von 1984*/ <<- neuer wert tu hanover
              uRcal : 2.2E-6; /*in lb aus Kalibschein 0187PTB05*/
              uR0cal : 1.0E-6; /*lb*/
              uk :462.0e-9;
              ut :0.16;

        """
        r_ind      = sym.Symbol('r_ind')
        u_b        = sym.Symbol('u_b')
        u_sys      = sym.Symbol('u_sys')
        r_0        = sym.Symbol('r_0')
        f          = sym.Symbol('f')
        A          = sym.Symbol('A')
        p_res      = sym.Symbol('p_res')
        m_cal      = sym.Symbol('m_cal')
        g          = sym.Symbol('g')
        r_cal      = sym.Symbol('r_cal')
        r_cal_0    = sym.Symbol('r_cal_0')
        ab         = sym.Symbol('ab')
        tem        = sym.Symbol('tem')
        rho_frs    = sym.Symbol('rho_frs')
        rho_gas    = sym.Symbol('rho_gas')

        p_frs = sym.S((r_ind+u_b+u_sys)/(r_cal-r_cal_0)
                      *m_cal*g/A/(1-rho_gas/rho_frs)/(1.0+ab*(tem-20.0)))

        s_r_ind      = sym.diff(p_frs, r_ind)
        s_u_b        = sym.diff(p_frs, u_b)
        s_u_sys      = sym.diff(p_frs, u_sys)
        s_r_cal      = sym.diff(p_frs, r_cal)
        s_r_cal_0    = sym.diff(p_frs, r_cal_0)
        s_m_cal      = sym.diff(p_frs, m_cal)
        s_g          = sym.diff(p_frs, g)
        s_A          = sym.diff(p_frs, A)
        s_ab         = sym.diff(p_frs, ab)
        s_tem        = sym.diff(p_frs, tem)
        s_rho_gas    = sym.diff(p_frs, rho_gas)
        s_rho_frs    = sym.diff(p_frs, rho_frs)


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
