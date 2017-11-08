import numpy as np
from scipy.interpolate import interp1d
from ..device.device import Device
from ..vpy_io import Io

class Cdg(Device):


    io = Io()
    log = io.log(__name__)
    log.info("start logging")

    unit              = "mbar"
    usable_decades    = 3
    max_typehead_mbar = {
                        "001Torr":  0.0013,
                        "01Torr":   0.0133,
                        "1Torr":    1.3332,
                        "10Torr":   13.332,
                        "100Torr":  133.32,
                        "1000Torr": 1333.2
                        }

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
        if "CalibrationObject" in dev:
            dev = dev['CalibrationObject']

        if "Setup" in dev:
            dev_setup = dev['Setup']
            if  "TypeHead" in dev_setup:
                th =  dev_setup['TypeHead']
                if th is not None:
                    self.max_p_mbar = self.max_typehead_mbar[th]
                    self.min_p_mbar = self.max_p_mbar/10.0**self.usable_decades

        if "Interpol" in dev:
            self.interpol_x   = self.get_value("p_ind", self.unit)
            self.interpol_y   = self.get_value("e", "1")
            self.interpol_min = np.min(self.interpol_x)
            self.interpol_max = np.max(self.interpol_x)

    def get_name(self):
        return self.doc['Name']

    def store_error_interpol(self, p, e, punit = "mbar", eunit="1"):
        interpol = [
                    {"Type":"p_ind",
                    "Unit": punit,
                    "Value":list(p)
                    },{
                    "Type":"e",
                    "Unit": eunit,
                    "Value":list(e)
                    }]
        if "CalibrationObject" in self.doc:
            self.doc['CalibrationObject']['Interpol'] = interpol

    def get_error_interpol(self, p, unit):
        if unit == self.unit:
            f = self.interp_function(self.interpol_x, self.interpol_y)

        return f(p)

    def interp_function(self, x, y):
        return interp1d(x, y, kind = "linear")

    def cal_error_interpol(self, pind, pcal, unit):
        if unit == self.unit:
            pcal, pind = self.cut_values(pcal, pind)
            x = pind
            y = pind / pcal - 1.0
            f = self.interp_function(x,y)
            nx = self.get_nice_vals(x)
            ny = f(nx)

            return nx , ny

    def cut_values(self, pcal, pind):
        i     = np.where(pcal < self.max_p_mbar)[0][-1]
        j     = np.where(pcal > self.min_p_mbar)[0][0]
        return pcal[j:i], pind[j:i]

    def get_nice_vals(self, x):
        ls    = np.logspace(-5, 3, num = 80)
        x_max = np.max(x)
        x_min = np.min(x)
        i     = np.where(ls > x_min)[0][0]
        j     = np.where(ls < x_max)[0][-1]

        return np.concatenate((np.array([x_min]), ls[i:j],  np.array([x_max])))

class InfCdg(Cdg):
    """Inficon CDGs are usable two decades only
    """

    usable_decades = 2

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
