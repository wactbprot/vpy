import numpy as np
from ..device.device import Device
from ..vpy_io import Io

class DmmSystemSwitch(Device):

    io = Io()
    log = io.log(__name__)
    log.info("start logging")



    def __init__(self, doc, dev):
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
