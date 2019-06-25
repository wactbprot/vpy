import numpy as np
from ..device.device import Device

class Dmm(Device):

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
        self.name = dev.get('Name') 
        self.log.debug("init func: {}".format(__name__))

    def get_name(self):
        return self.doc['Name']

    def uncert_temperature(self, t, tunit, runit="K"):
        """calculates the uncertainty of the temperature measurement

        """
        u1 = self.get_value("u1", "K")
        u2 = self.get_value("u2", "K")
        u3 = self.get_value("u3", "K")
        u4 = self.get_value("u4", "K")
        u5 = self.get_value("u5", "K")
        u6 = self.get_value("u6", "K")

        return np.sqrt(u1**2 +u2**2 + u3**2 +u4**2 +u5**2 +u6**2)
