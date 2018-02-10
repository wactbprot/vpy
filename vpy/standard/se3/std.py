import copy
import numpy as np
from ...vpy_io import Io
from ...device.dmm import Dmm
from ...device.cdg import InfCdg
from ...constants import Constants
from ...calibration_devices import  CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe3
from ..standard import Standard
from ..group_normal import GroupNormal
from ...device.cdg  import Cdg

class Se3(Standard):
    """Configuration and methodes of static expansion system Se3.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpos.

    """
    name = "SE3"
    unit = "mbar"

    def __init__(self, doc):

        doc = copy.deepcopy(doc)
        super().__init__(doc, self.name)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxSe3(doc)

        self.TDev = Dmm(doc, self.Cobj.get_by_name("SE3_Temperature_Keithley"))
        self.GN   = GroupNormal(doc, (
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_1T_1")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_1T_2")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_1T_3")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_10T_1")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_10T_2")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_10T_3")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_100T_1")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_100T_2")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_100T_3")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_1000T_1")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_1000T_2")),
                                    InfCdg(doc, self.Cobj.get_by_name("CDG_1000T_3"))
                                    ))

    def define_model(self):
        """ Defines symbols and model for the static expansion system SE3.
        The order of symbols must match the order in ``gen_val_arr``:

        #. p_fill
        #. f_corr
        #. p_before
        #. p_after
        #. V_5
        #. V_add

        The equation is:

        .. math::

                p = f_{corr} p_{fill}

        with

        .. math::

                f_{corr} = \\frac{1}{ \\frac{1}{f} + \\frac{V_{add}}{V_{start}}}

        and

        .. math::

                V_{add} = \\frac{V_5}{p_{after}/p_{before} - 1}

        :type: class
        """
        f          = sym.Symbol('f')
        p_fill     = sym.Symbol('p_fill')
        V_5        = sym.Symbol('V_5')
        p_before   = sym.Symbol('p_before')
        p_after    = sym.Symbol('p_after')

        self.symb = (
                    f,
                    p_fill,
                    V_5,
                    p_before,
                    p_after
                    )

        #self.model_f_corr =
        self.model        = p_fill * f_corr

    def get_name(self):
        """Returns the name of the Standard.
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
