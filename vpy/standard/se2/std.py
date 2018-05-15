import numpy as np
from ...device.qbs import Qbs
from ...device.dmm import Dmm
from ...calibration_devices import CalibrationObject
from ...values import AuxSe2
from ..standard import Standard
from ...device.cdg import Cdg

class Se2(Standard):
    """Configuration and methodes of static expansion system Se2.
    """
    name = "SE2"
    unit = "mbar"

    def __init__(self, doc):
        super().__init__(doc, self.name)

        self.Aux = AuxSe2(doc)
        self.TDev = Dmm(doc, self.Cobj.get_by_name("SE2_DMM_Keithley"))
        self.Qbs = Qbs(doc, self.Cobj.get_by_name("SE2_Ruska"))

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
