import numpy as np
import sympy as sym
from ..standard import Standard
from ...device.srg import Srg
from ...constants import Constants
from ...calibration_devices import CalibrationObject
from ...values import Temperature, Pressure, Time


class Ce3(Standard):
    """Calculation methods of FM3 and CE3."""
    name = "CE3"
    unit = "mbar"

    def __init__(self, doc):
        super().__init__(doc, self.name)
        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)

        # residual pressure device
        amt = self.Time.get_value("start_sz_mt", "ms")
        self.no_of_meas_points = len(amt)
