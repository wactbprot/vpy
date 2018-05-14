import copy
import json
import numpy as np
import sympy as sym
from ...device.dmm import Dmm
from ...device.cdg import InfCdg
from ...constants import Constants
from ...calibration_devices import  CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe3, OutGasRate, Position
from ..standard import Standard
from ...device.cdg  import Cdg

class Se3(Standard):
    """Configuration and methodes of static expansion system SE3.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpose if doc is a calibration. For the analysis of
    state measurements ``amt`` is used.
    """
    name = "SE3"
    unit = "mbar"

    def __init__(self, doc):
        super().__init__(doc, self.name)

        with open('./vpy/standard/se3/values.json') as valf:
            self.val_conf = json.load(valf)

        with open('./vpy/standard/se3/aux_values.json') as auxf:
            self.aux_val_conf = json.load(auxf)

        with open('./vpy/standard/se3/state.json') as statef:
            self.state_check = json.load(statef)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxSe3(doc)

        if 'State' in doc:
            self.OutGas = OutGasRate(doc)
            self.no_of_meas_points = len(self.Time.get_value("amt", "ms"))

        if 'Calibration' in doc:
            # define model
            self.Pos = Position(doc)
            self.no_of_meas_points = len(self.Time.get_value("amt_fill", "ms"))
            self.define_model()


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


        :type: class
        """
        self.model_unit = "mbar"

        f         = sym.Symbol('f')
        p_fill    = sym.Symbol('p_fill')
        V_start   = sym.Symbol('V_start')
        V_add     = sym.Symbol('V_add')
        T_before  = sym.Symbol('T_before')
        T_after   = sym.Symbol('T_after')
        rg        = sym.Symbol('rg')

        self.symb = (
                    f,
                    p_fill,
                    V_start,
                    V_add,
                    T_before,
                    T_after,
                    rg,
                    )

        self.model = p_fill*1.0/(1.0/f+V_add/V_start)/T_before*T_after/rg

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as define_models symbols order:

        #. f
        #. p_fill
        #. V_5
        #. V_start
        #. V_add
        #. T_before
        #. T_after

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        self.gen_val_dict(res)
        self.val_arr = [
                    self.val_dict['f'],
                    self.val_dict['p_fill'],
                    self.val_dict['V_start'],
                    self.val_dict['V_add'],
                    self.val_dict['T_before'],
                    self.val_dict['T_after'],
                    self.val_dict['rg'],
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

        self.val_dict = {
        'f': res.pick("Expansion", "uncorr","1"),
        'p_fill':res.pick("Pressure", "fill", self.unit),
        'V_start':res.pick("Volume", "start", "cm^3"),
        'V_add': res.pick("Volume", "add", "cm^3"),
        'T_before':res.pick("Temperature", "before", "K"),
        'T_after':res.pick("Temperature", "after", "K"),
        'rg':res.pick("Correction", "rg", "1"),
        }

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

    def get_expansion_name(self):
        """Returns an np.array containing
        the expansion name (``f_s``, ``f_m`` or ``f_l``)
        of the length: ``self.no_of_meas_points```

        :returns: array of expansion names
        :rtype: np.array of strings
        """

        f = self.Aux.get_expansion()
        if f is not None:
            return np.full(self.no_of_meas_points, f)

    def expansion(self, res):
        """Builds a vector containing the expansion factors
        and stores it.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        f  = np.full(self.no_of_meas_points, None)
        f_name  = self.get_expansion_name()
        i_s    = np.where(f_name == "f_s")
        i_m    = np.where(f_name == "f_m")
        i_l    = np.where(f_name == "f_l")

        if np.shape(i_s)[1] > 0:
            f[i_s]       = self.get_value("f_s","1")

        if np.shape(i_m)[1] > 0:
            f[i_m]       = self.get_value("f_m","1")

        if np.shape(i_l)[1] > 0:
            f[i_l]       = self.get_value("f_l","1")

        res.store("Expansion", "uncorr", f, "1")
