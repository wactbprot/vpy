import numpy as np
from ..device.device import Device
from ..vpy_io import Io

class Dmm(Device):

    def __init__(self, doc, dev):
        super().__init__(doc, dev)
        self.log.debug("init func: {}".format(__name__))

    def get_name(self):
        return self.doc['Name']
