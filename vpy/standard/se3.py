import copy
import numpy as np
from ..vpy_io import Io
from ..document import Document
from ..device.dmm_system_switch import DmmSystemSwitch
from ..device.cdg import InfCdg
from ..constants import Constants
from ..calibration_devices import  CalibrationObject
from ..values import Temperature, Pressure, Time, AuxSe3
from ..standard.standard import Standard
from ..standard.group_normal import GroupNormal
from ..device.cdg  import Cdg

class Se3(Standard):
    """Configuration and methodes of static expansion system Se3.
    """

    name = "SE3"
    unit = "mbar"

    io = Io()
    log = io.logger(__name__)
    log.info("start logging")

    def __init__(self, orgdoc):

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


    def pressure_nd(self, res):
        """Stores the differential pressure of the zero indicator:

        *Pressure, nd, mbar*
        """
        p_nd_off = self.Pres.get_value("nd_offset", "mbar")
        p_nd_ind = self.Pres.get_value("nd_ind", "mbar")

        res.store("Pressure" ,"nd", p_nd_ind - p_nd_off , "mbar")

    def pressure_fill(self, res):
        """Calculates the mean value of the filling pressure by means of
        *GroupNormal* methods.

         *Pressure, fill, mbar*
        """
        chs = [
            "1T_1","1T_2","1T_3",
            "10T_1","10T_2","10T_3",
            "100T_1","100T_2","100T_3",
            "1000T_1","1000T_2","1000T_3"
            ]
        N = len(chs)

        p_ind_arr = self.Pres.get_array("", chs, "-fill","mbar")
        meas_time = self.Time.get_value("amt_fill", "ms")

        for i in range(N):
            chnm = "{}-offset".format(chs[i])
            vec  = self.Aux.get_val_by_time(meas_time, "offset_mt", "ms", chnm, "mbar")
            M    = len(vec)
            if i == 0:
                p_off_arr = np.full((N, M), np.nan)

            p_off_arr[i][:] = vec[:]

        p_arr     = p_ind_arr - p_off_arr
        e_arr     = self.GN.get_error_iterpol(p_arr, "mbar")
        p_cor_arr = p_arr/(e_arr + 1.0)
        p_fill    = self.GN.cal_mean_pressure(p_cor_arr, "mbar" )

        res.store("Pressure" ,"fill", p_fill , "mbar")

    def temperature_before(self, res):
        """Calculates the temperature of the starting volumes.

        *Temperature, before, K*
        """

        tem = self.temperature_volume_m()
        res.store("Temperature" ,"before", tem , "K")

    def temperature_after(self, res):
        """Calculates the temperature of the end volume.

        *Temperature, after, K*
        """

        tem = self.temperature_vessel()
        res.store("Temperature","after", tem , "K")

    def temperature_volume_m(self):
        """Temperature of the medium (0.2l) volume. The used  sensors are:

        *channel 3004 to 3013*
        """
        chs     = list(range(3004, 3013))
        tem_arr = self.Temp.get_array("ch_", chs, "_before", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)

    def temperature_vessel(self):
        """Temperature of the medium (0.2l) volume. The used  sensors are:

        *channel 1001 to 1030* and *channel 2001 to 2028*
        """
        chs = list(range(1001, 1030)) + list(range(2001, 1028))

        tem_arr = self.Temp.get_array("ch_", chs, "_before", "C")
        cor_arr = self.TDev.get_array("corr_ch_", chs, "", "K")
        conv    = self.Cons.get_conv("C", "K")

        return np.mean(tem_arr + cor_arr + conv, axis=0)
