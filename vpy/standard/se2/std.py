import numpy as np
from ...device.qbs import Qbs
from ...device.dmm import Dmm
from ...constants import Constants
from ...calibration_devices import  CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe2
from ..standard import Standard
from ...device.cdg  import Cdg

class Se2(Standard):
    """Configuration and methodes of static expansion system Se3.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpos.

    """
    name = "SE2"
    unit = "mbar"

    def __init__(self, doc):
        super().__init__(doc, self.name)

                # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxSe2(doc)

        self.TDev    = Dmm(doc, self.Cobj.get_by_name("SE2_DMM_Keithley"))
        self.TDevAdd = Dmm(doc, self.Cobj.get_by_name("FM3_CE3-DMM_Agilent"))
        self.Qbs     = Qbs(doc, self.Cobj.get_by_name("SE2_Ruska"))

        self.log.debug("init func: {}".format(__name__))

    def get_name(self):
        """Returns the name of the standard.
        """
        return self.name

    def get_gas(self):
        """Returns the name of the calibration gas.

        .. todo::

                get gas from todo if nothing found in AuxValues

        :returns: gas (N2, He etc.)
        :rtype: str
        """

        gas = self.Aux.get_gas()
        if gas is not None:
            return gas

    def define_model_p(self):
        """ Defines symbols and model calibration pressure.
        The order of symbols must match the order in ``gen_val_arr``:
        The equation is:

        .. math::
                p=f_i p_{fill} \\frac{T_{after}}{T_{before}} c_{rg}

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        f_i       = sym.Symbol('f_i')
        p_fill    = sym.Symbol('p_fill')
        T_before  = sym.Symbol('T_before')
        T_after   = sym.Symbol('T_after')
        rg        = sym.Symbol('rg')
        self.symb = (
                    p_fill,
                    T_before,
                    T_after,
                    f_i,
                    rg,
                    )
        self.model = f_i*p_fill*T_after/T_before*rg

    def define_model_f(self):
        """ Defines symbols and model for the determination of the
        expansion ratios f.
        The order of symbols must match the order in ``gen_val_arr``:
        The equation is:

            .. math::
                p=f_i p_{fill} \\frac{T_{after}}{T_{before}} c_{rg}

            :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
            :type: class
        """

        p_fill    = sym.Symbol('p_fill')
        p_frs     = sym.Symbol('p_frs')
        p_nd      = sym.Symbol('p_nd')
        T_before  = sym.Symbol('T_before')
        T_after   = sym.Symbol('T_after')
        rg        = sym.Symbol('rg')

        self.symb = (
                    p_fill,
                    p_frs,
                    p_nd,
                    T_before,
                    T_after,
                    rg)

        self.model = (p_frs-p_nd)/p_fill*T_before/T_after/rg
