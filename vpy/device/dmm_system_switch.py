import numpy as np
from ..device.device import Device
from ..vpy_io import Io

class DmmSystemSwitch(Device):





    def __init__(self, doc, dev):
        self.log = Io().logger(__name__)
        self.log.info("start logging")
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
