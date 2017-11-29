import copy
import numpy as np
from ...vpy_io import Io
from ...device.qbs import Qbs
from ...device.dmm import Dmm
from ...constants import Constants
from ...calibration_devices import  CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe2
from ..standard import Standard
from ..group_normal import GroupNormal
from ...device.cdg  import Cdg

class Se2(Standard):
    """Configuration and methodes of static expansion system Se3.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpos.

    """
    name = "SE2"
    unit = "mbar"

    def __init__(self, orgdoc):
        
        super().__init__(orgdoc, self.name)
        doc = copy.deepcopy(orgdoc)

        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxSe2(doc)

        self.TDev    = Dmm(doc, self.Cobj.get_by_name("SE2_DMM_Keithley"))
        self.TDevAdd = Dmm(doc, self.Cobj.get_by_name("FM3_CE3-DMM_Agilent"))
        self.Qbs     = Qbs(doc, self.Cobj.get_by_name("SE2_Ruska"))

        self.no_of_meas_points = len(self.Time.get_value("amt_fill", "ms"))

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
