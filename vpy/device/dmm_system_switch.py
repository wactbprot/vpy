import numpy as np
from ..device.device import Device
from ..vpy_io import Io

class DmmSystemSwitch(Device):

    def __init__(self, doc, dev):
        
        self.log.debug("init func: {}".format(__name__))

        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
