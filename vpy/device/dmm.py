import numpy as np
from ..device.device import Device
from ..vpy_io import Io

class Dmm(Device):

    def __init__(self, doc, dev):
        io = Io()
        self.log = io.logger(__name__)
        self.log.debug("init func: {}".format(__name__))

        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
