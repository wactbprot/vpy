import copy
import json
import numpy as np
import sympy as sym
from ...device.dmm import Dmm
from ...device.cdg import InfCdg
from ...constants import Constants
from ...calibration_devices import CalibrationObject
from ...values import Temperature, Pressure, Time, AuxDkmPpc4, Mass
from ..standard import Standard
from ...device.cdg import Cdg


class DkmPpc4(Standard):
    """Configuration and methodes new rotary piston gauge.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpose if doc is a calibration. For the analysis of
    state measurements ``amt`` is used.
    """
    name = 'DKM_PPC4'
    unit = 'Pa'

    def __init__(self, doc):
        super().__init__(doc, self.name)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Mass = Mass(doc)
        self.Aux = AuxDkmPpc4(doc)
        self.no_of_meas_points = len(self.Time.get_value("amt_meas", "ms"))
        self.TDev = Dmm(doc, self.Cobj.get_by_name("DKM_PPC4_DMM"))

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
