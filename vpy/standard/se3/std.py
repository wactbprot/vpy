import copy
import json
import numpy as np
import sympy as sym
from ...device.dmm import Dmm
from ...device.cdg import InfCdg
from ...constants import Constants
from ...calibration_devices import CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe3, OutGasRate, Position
from ..standard import Standard
from ...device.cdg import Cdg


class Se3(Standard):
    """Configuration and methodes of static expansion system SE3.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpose if doc is a calibration. For the analysis of
    state measurements ``amt`` is used.
    """
    name = "SE3"
    unit = "mbar"
    temp_dev_name = "SE3_Temperature_Keithley"
    small_temp_types = ["ch_3001_before", "ch_3002_before", "ch_3003_before", ]

    medium_temp_types = ["ch_3004_before", "ch_3005_before", "ch_3006_before",
                        "ch_3007_before", "ch_3008_before", "ch_3009_before",
                        "ch_3010_before", "ch_3011_before", "ch_3012_before",
                        "ch_3013_before", ]

    large_temp_types = ["ch_3014_before", "ch_3015_before", "ch_3016_before",
                        "ch_3017_before", "ch_3018_before", "ch_3019_before",
                        "ch_3020_before", "ch_3021_before", "ch_3022_before",
                        "ch_3023_before", "ch_3024_before", "ch_3025_before",
                        "ch_3026_before", "ch_3027_before", "ch_3028_before",
                        "ch_3029_before", "ch_3030_before", ]

    vessel_temp_types = ["ch_1001_after", "ch_1002_after", "ch_1003_after",
                        "ch_1004_after", "ch_1005_after", "ch_1006_after",
                        "ch_1007_after", "ch_1008_after", "ch_1009_after",
                        "ch_1010_after", "ch_1011_after", "ch_1012_after",
                        "ch_1013_after", "ch_1014_after", "ch_1015_after",
                        "ch_1016_after", "ch_1017_after", "ch_1018_after",
                        "ch_1019_after", "ch_1020_after", "ch_1020_after",
                        "ch_1021_after", "ch_1022_after", "ch_1023_after",
                        "ch_1024_after", "ch_1025_after", "ch_1026_after",
                        "ch_1027_after", "ch_1028_after", "ch_1029_after",
                        "ch_1030_after", "ch_2001_after", "ch_2002_after",
                        "ch_2003_after", "ch_2004_after", "ch_2005_after",
                        "ch_2006_after", "ch_2007_after", "ch_2008_after",
                        "ch_2009_after", "ch_2010_after", "ch_2011_after",
                        "ch_2012_after", "ch_2013_after", "ch_2014_after",
                        "ch_2015_after", "ch_2016_after", "ch_2017_after",
                        "ch_2018_after", "ch_2019_after", "ch_2020_after",
                        "ch_2020_after", "ch_2021_after", "ch_2022_after",
                        "ch_2023_after", "ch_2024_after", "ch_2025_after",
                        "ch_2026_after", "ch_2027_after", "ch_2028_after", ]

    fill_dev_names = ["CDG_1T_1",  "CDG_1T_2", "CDG_1T_3",
                    "CDG_10T_1",  "CDG_10T_2",  "CDG_10T_3",
                    "CDG_100T_1", "CDG_100T_2", "CDG_100T_3",
                    "CDG_1000T_1", "CDG_1000T_2", "CDG_1000T_3", ]

    fill_types = ["1T_1-fill", "1T_2-fill", "1T_3-fill",
                  "10T_1-fill",  "10T_2-fill", "10T_3-fill",
                  "100T_1-fill", "100T_2-fill", "100T_3-fill",
                  "1000T_1-fill", "1000T_2-fill", "1000T_3-fill", ]

    offset_types = ["1T_1-offset", "1T_2-offset", "1T_3-offset",
                    "10T_1-offset",  "10T_2-offset", "10T_3-offset",
                    "100T_1-offset", "100T_2-offset", "100T_3-offset",
                    "1000T_1-offset", "1000T_2-offset", "1000T_3-offset", ]

    def __init__(self, doc):
        super().__init__(doc, self.name)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux = AuxSe3(doc)
        self.Pos = Position(doc)

        if 'State' in doc:
            self.OutGas = OutGasRate(doc)
            self.no_of_meas_points = len(self.Time.get_value("amt", "ms"))

        if 'Calibration' in doc:
            # define model
            self.no_of_meas_points = len(self.Time.get_value("amt_fill", "ms"))
            self.define_model()

        self.TDev = Dmm(doc, self.Cobj.get_by_name(self.temp_dev_name))

        self.FillDevs =[]
        for d in self.fill_dev_names:
            self.FillDevs.append(InfCdg(doc, self.Cobj.get_by_name(d)))


    def define_model(self):
        """ Defines symbols and model for the static expansion system SE3.
        The order of symbols must match the order in ``gen_val_arr``:

        # . f
        # . p_fill
        # . V_5
        # . V_start
        # . p_before
        # . p_after

        The equation is:

        .. math::

                p = f_{corr} p_{fill}

        with

        .. math::

                f_{corr} = \\frac{1}{ \\frac{1}{f} + \\frac{V_{add}}{V_{start}}}


        :type: class
        """
        self.model_unit="mbar"

        f=sym.Symbol('f')
        p_fill=sym.Symbol('p_fill')
        V_start=sym.Symbol('V_start')
        V_add=sym.Symbol('V_add')
        T_before=sym.Symbol('T_before')
        T_after=sym.Symbol('T_after')
        rg=sym.Symbol('rg')

        self.symb=(
                    f,
                    p_fill,
                    V_start,
                    V_add,
                    T_before,
                    T_after,
                    rg,
                    )

        self.model=p_fill * 1.0 / (1.0 / f + V_add / V_start) / T_before * T_after / rg

    def gen_val_array(self, res):
        """Generates a array of values
        with the same order as define_models symbols order:

        # . f
        # . p_fill
        # . V_5
        # . V_start
        # . V_add
        # . T_before
        # . T_after

        :param: Class with methode
            store(quantity, type, value, unit, [stdev], [N])) and
            pick(quantity, type, unit)
        :type: class
        """

        self.gen_val_dict(res)
        self.val_arr=[
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

        self.val_dict={
        'f': res.pick("Expansion", "uncorr", "1"),
        'p_fill': res.pick("Pressure", "fill", self.unit),
        'V_start': res.pick("Volume", "start", "cm^3"),
        'V_add': res.pick("Volume", "add", "cm^3"),
        'T_before': res.pick("Temperature", "before", "K"),
        'T_after': res.pick("Temperature", "after", "K"),
        'rg': res.pick("Correction", "rg", "1"),
        }

    def get_gas(self):
        """Returns the name of the calibration gas.

        .. todo::

                get gas from todo if nothing found in AuxValues

        :returns: gas (N2, He etc.)
        :rtype: str
        """

        gas=self.Aux.get_gas()
        if gas is not None:
            return gas

    def get_expansion_name(self):
        """Returns an np.array containing
        the expansion name (``f_s``, ``f_m`` or ``f_l``)
        of the length: ``self.no_of_meas_points```

        :returns: array of expansion names
        :rtype: np.array of strings
        """

        f=self.Aux.get_expansion()
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

        f=np.full(self.no_of_meas_points, np.nan)
        f_name=self.get_expansion_name()
        i_s=np.where(f_name == "f_s")
        i_m=np.where(f_name == "f_m")
        i_l=np.where(f_name == "f_l")

        if np.shape(i_s)[1] > 0:
            f[i_s]=self.get_value("f_s", "1")

        if np.shape(i_m)[1] > 0:
            f[i_m]=self.get_value("f_m", "1")

        if np.shape(i_l)[1] > 0:
            f[i_l]=self.get_value("f_l", "1")

        res.store("Expansion", "uncorr", f, "1")
