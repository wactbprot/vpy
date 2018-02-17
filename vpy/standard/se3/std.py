import copy
import json
import numpy as np
import sympy as sym
from ...device.dmm import Dmm
from ...device.cdg import InfCdg
from ...constants import Constants
from ...calibration_devices import  CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe3
from ..standard import Standard
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

        # define model
        self.define_model()
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

        self.log.debug("init func: {}".format(__name__))

    def define_model(self):
        """ Defines symbols and model for the static expansion system SE3.
        The order of symbols must match the order in ``gen_val_arr``:

        #. f
        #. p_fill
        #. V_5
        #. V_start
        #. p_before
        #. p_after

        The equation is:

        .. math::

                p = f_{corr} p_{fill}

        with

        .. math::

                f_{corr} = \\frac{1}{ \\frac{1}{f} + \\frac{V_{add}}{V_{start}}}

        and

        .. math::

                V_{add} = \\frac{V_5}{p_{ratio} - 1}

        and

                p_{ratio} = p_{after}/p_{before}

        :type: class
        """
        f          = sym.Symbol('f')
        p_fill     = sym.Symbol('p_fill')
        V_5        = sym.Symbol('V_5')
        V_start    = sym.Symbol('V_start')
        p_ratio    = sym.Symbol('p_ratio')

        self.symb = (
                    f,
                    p_fill,
                    V_5,
                    V_start,
                    p_ratio,
                    )

        V_add   = V_5/(p_ratio - 1.0)
        f_corr  = 1.0/(1.0/f + V_add/V_start)

        self.model_V_add = V_add
        self.model       = p_fill * f_corr

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as define_models symbols order:

        #. f
        #. p_fill
        #. V_5
        #. V_start
        #. p_ratio

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        self.gen_val_dict(res)
        self.val_arr = [
                    self.val_dict['f'],
                    self.val_dict['p_fill'],
                    self.val_dict['V_5'],
                    self.val_dict['V_start'],
                    self.val_dict['p_ratio'],
                    ]

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

        V_start = np.full(self.no_of_meas_points, np.nan)
        f       = np.full(self.no_of_meas_points, np.nan)
        f_name  = self.get_expansion()

        idxs    = np.where(f_name == "f_s")
        if np.shape(idxs)[1] > 0:
            V_start[idxs] = self.get_value("V_s","cm^3")
            f[idxs]       = self.get_value("f_s","1")

        idxm    = np.where(f_name == "f_m")
        if np.shape(idxm)[1] > 0:
            V_start[idxm] = self.get_value("V_m","cm^3")
            f[idxm]       = self.get_value("f_m","1")


        idxl    = np.where(f_name == "f_l")
        if np.shape(idxl)[1] > 0:
            V_start[idxl] = self.get_value("V_l","cm^3")
            f[idxl]       = self.get_value("f_l","1")

        self.val_dict = {
        'f': f,
        'p_fill':res.pick("Pressure", "fill", self.unit),
        'V_5':np.full(self.no_of_meas_points,self.get_value("V_5","cm^3")),
        'V_start':V_start,
        'p_ratio': self.Aux.get_press_ratio(self.no_of_meas_points),
        }

    def get_expansion(self):

        f = self.Aux.get_expansion()

        if f is None:
            pass # get expansion from values
        else:
            f = np.full(self.no_of_meas_points, f)

        return f

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
