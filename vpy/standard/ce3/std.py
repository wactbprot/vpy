import numpy as np
import sympy as sym
from ..standard import Standard
from ...device.srg import Srg
from ...device.cdg import InfCdg, Cdg
from ...constants import Constants
from ...calibration_devices import CalibrationObject
from ...values import Temperature, Pressure, Time, Drift, AuxValues


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
        self.Drift = Drift(doc)
        self.Aux = AuxValues(doc)

        amt = self.Time.get_value("start_sz_mt", "ms")
        self.no_of_meas_points = len(amt)
        self.opk = self.Aux.doc.get("OperationKind")
        self.gas = self.Aux.doc.get("Gas")

        ## CDGA ... 10Torr
        self.cdga_lim_x001 = 0.1
        self.cdga_lim_x01 = 1.33
        self.cdga_lim_x1 = 13.33

        self.CDGA = Cdg(doc, self.Cobj.get_by_name("FM3_10T_NEW"))


        ## CDGB ... 1000mbar
        self.cdgb_lim_x001 = 13.33
        self.cdgb_lim_x01 = 133.3
        self.cdgb_lim_x1 = 1333.

        self.CDGB = Cdg(doc, self.Cobj.get_by_name("FM3_1000mbar"))

        ## CDGD ... 0.1Torr
        self.cdgd_lim_x01 = 0.0133
        self.cdgd_lim_x1 = 0.1333
