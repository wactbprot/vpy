import copy
import numpy as np
from ...vpy_io import Io
from ...device.dmm_system_switch import DmmSystemSwitch
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

    def __init__(self, orgdoc):
        self.log = Io().logger(__name__)

        super().__init__(orgdoc, self.name)
        doc = copy.deepcopy(orgdoc)

        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux  = AuxSe3(doc)

        self.TDev = DmmSystemSwitch(doc, self.Cobj.get_by_name("SE3_Temperature_Keithley"))
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
