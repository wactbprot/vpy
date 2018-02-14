import copy
import json
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
        super().__init__(doc, self.name)

        with open('./vpy/standard/se3/values.json') as valf:
            self.val_conf = json.load(valf)

        with open('./vpy/standard/se3/aux_values.json') as auxf:
            self.aux_val_conf = json.load(auxf)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxSe3(doc)

        self.no_of_meas_points = len(self.Time.get_value("amt_fill", "ms"))

        self.TDev  = Dmm(doc, self.Cobj.get_by_name("SE3_Temperature_Keithley"))

        self.FillDevs = []
        for val in self.val_conf["Pressure"]["Fill"]:
            self.FillDevs.append(InfCdg(doc, self.Cobj.get_by_name(val["DevName"])))

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
        V_start    = sym.Symbol('V_start')
        p_before   = sym.Symbol('p_before')
        p_after    = sym.Symbol('p_after')

        self.symb = (
                    f,
                    p_fill,
                    V_5,
                    V_start,
                    p_before,
                    p_after
                    )
        V_add  = V_start/(p_before/p_after -1)
        f_corr = 1.0/(1.0/f + V_add/V_start)

        self.model_V_add = V_add
        self.model        = p_fill * f_corr

    def gen_val_dict(self, res):
        """Reads in a dict of values
        with the same order as in ``define_models``. For the calculation
        of the gas density, the Frs reading is multiplyed by 10 which gives a
        suffucient approximation for the pressure.

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """
        self.model_unit = "mbar"

        p_fill = res.pick("Pressure", "fill", self.unit)

        V_5        = self.get_value("V5","cm^3")
        V_s        = self.get_value("Vm","cm^3")
        V_m        = self.get_value("Vs","cm^3")
        V_l        = self.get_value("Vl","cm^3")

        f = self.Aux.get_expansion()
        if f is None:
            pass # get expansion from values
        else:
            f = np.full(self.no_of_meas_points, f)

        if f == "fs":
            V_start = const_V_s

        if f == "fm":
            V_start = const_V_m

        if f == "fl":
            V_start = const_V_l

        self.val_dict = {
        'f': f ,
        'p_fill':pfill,
        'V_5':V_5,
        'V_start':V_start,
        'p_before': self.Aux.get_value("add_before", "V"),
        'p_after': self.Aux.get_value("add_after", "V"),
        }

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
