import numpy as np
import sympy as sym
from ..standard import Standard
from ...device.srg import Srg
from ...constants import Constants
from ...calibration_devices import CalibrationObject
from ...values import Temperature, Pressure, Time, AuxFrs5, Range


class Frs5(Standard):
    """Calculation methods of large area piston gauge FRS5.

            * ``p_frs``    ... abs. pressure of the piston gauge [p]=Pa
            * ``r``        ... reading [r] = lb
            * ``u_b``      ... standard uncertainty of the balance [u_b] = lb
            * ``u_sys``    ... sys. uncertanty of the balance [u_sys]=lb
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
    name = "FRS5"
    unit = "Pa"
    
    def __init__(self, doc):
        super().__init__(doc, self.name)
        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Range = Range(doc)
        self.Time = Time(doc)
        self.Aux = AuxFrs5(doc)
        
        # residual pressure device
        amt = self.Time.get_value("amt_meas", "ms")
        self.no_of_meas_points = len(amt)
        self.ResDev = Srg(doc, self.Cobj.get_by_name("FRS5_4019"))
        self.log.debug("init func: {}".format(__name__))

    def get_gas(self):
        """Returns the name of the calibration gas stored in *AuxValues*

        .. todo::

                implementation of aux.gas needed

        """

        self.log.warn("Default gas N2 used")
        return "N2"
