import copy
import numpy as np
import sympy as sym

from ... vpy_io import Io
from ..standard import Standard
from ...device.srg import Srg
from ...constants import Constants
from ...calibration_devices import  CalibrationObject
from ...values import Temperature, Pressure, Time, AuxFrs5


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
    name  = "FRS5"
    unit  = "mbar"


    def __init__(self, orgdoc):
        super().__init__(orgdoc, self.name)

        self.log = Io().logger(__name__)

        doc = copy.deepcopy(orgdoc)
        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxFrs5(doc)

        # residua pressure device
        self.ResDev = Srg(doc, self.Cobj.get_by_name("FRS55_4019"))
        self.no_of_meas_points = len(self.Time.get_value("amt_frs5_ind", "ms"))


    def get_gas(self):
        """Returns the name of the calibration gas stored in *AuxValues*

        .. todo::

                implementation of aux.gas needed

        """

        self.log.warn("Default gas N2 used")
        return "N2"

    def define_model(self, res):
        """ Defines symbols and model for FRS5.
        The order of symbols must match the order in ``gen_val_arr``:

        #. A
        #. r
        #. r_zc
        #. r_zc0
        #. r_cal
        #. r_cal0
        #. ub
        #. usys
        #. p_res
        #. m_cal
        #. g
        #. T
        #. rho_frs
        #. rho_gas
        #. ab

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        A          = sym.Symbol('A')
        r          = sym.Symbol('r')
        r_zc       = sym.Symbol('r_zc')
        r_zc0      = sym.Symbol('r_zc0')
        r_cal      = sym.Symbol('r_cal')
        r_cal0     = sym.Symbol('r_cal0')
        ub         = sym.Symbol('ub')
        usys       = sym.Symbol('usys')
        m_cal      = sym.Symbol('m_cal')
        g          = sym.Symbol('g')
        rho_frs    = sym.Symbol('rho_frs')
        rho_gas    = sym.Symbol('rho_gas')
        ab         = sym.Symbol('ab')
        T          = sym.Symbol('T')
        p_res      = sym.Symbol('p_res')

        self.symb = (
                    A,
                    r,
                    r_zc,
                    r_zc0,
                    r_cal,
                    r_cal0,
                    ub,
                    usys,
                    m_cal,
                    g,
                    rho_frs,
                    rho_gas,
                    ab,
                    T,
                    p_res,)

        self.sym_corr_buoyancy    = sym.S(1.0/(1.0-rho_gas/rho_frs))

        self.sym_corr_temperature = sym.S(1.0/(1.0+ab*(T-20.0)))

        self.sym_conv             = sym.S(m_cal/r_cal*g/A
                                            *self.sym_corr_buoyancy
                                            *self.sym_corr_temperature)

        self.sym_reading_offset   = r_zc-r_zc0

        self.model                = sym.S((r-self.sym_reading_offset+ub+usys)
                                            *self.sym_conv
                                            +p_res)

    def gen_val_dict(self, res):
        """Reads in a dict of values
        with the same order as ``define_models`` symbols order:

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        self.val_dict={
                        'A':      self.get_value("A_eff","m^2"),
                        'r':      self.Pres.get_value("frs_p", "lb"),
                        'r_zc':   self.Pres.get_value("frs_zc_p", "lb"),
                        'r_zc0':  self.Aux.get_val_by_time(self.Time.get_value("amt_frs5_ind", "ms"),
                                                            "offset_mt", "ms", "frs_zc0_p", "lb"),
                        'r_cal':  self.get_value("R_cal","lb"),
                        'rcal0':  np.full(self.no_of_meas_points, 0.0),
                        'ub':     np.full(self.no_of_meas_points, 0.0),
                        'usys':   np.full(self.no_of_meas_points, 0.0),
                        'm_cal':  self.get_value("m_cal","kg"),
                        'g':      self.get_value("g_frs","m/s^2"),
                        'rho_frs':self.get_value("rho_frs", "kg/m^3"),
                        'rho_gas':self.get_value("rho_gas","kg/m^3"),
                        'ab':     self.get_value("alpha_beta_frs", "1/C"),
                        'T':      res.pick("Temperature", "frs5", "C"),
                        'p_res':  res.pick("Pressure", "frs5_res", self.unit)
                        }

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as define_models symbols order:

        #. A
        #. r
        #. r_zc
        #. r_zc0
        #. r_cal
        #. r_cal0
        #. ub
        #. usys
        #. m_cal
        #. g
        #. rho_frs
        #. rho_gas
        #. ab
        #. T
        #. p_res

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        self.gen_val_dict(res)
        self.val_arr = [
                        self.val_dict['A'],
                        self.val_dict['r'],
                        self.val_dict['r_zc'],
                        self.val_dict['r_zc0'],
                        self.val_dict['r_cal'],
                        self.val_dict['rcal0'],
                        self.val_dict['ub'],
                        self.val_dict['usys'],
                        self.val_dict['m_cal'],
                        self.val_dict['g'],
                        self.val_dict['rho_frs'],
                        self.val_dict['rho_gas'],
                        self.val_dict['ab'],
                        self.val_dict['T'],
                        self.val_dict['p_res'],
                ]
