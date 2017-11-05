import numpy as np
from ..device.device import Device
from ..log import log

class DmmSystemSwitch(Device):

    log = log().getLogger(__name__)
    log.info("Document class ini")


    def __init__(self, doc, dev):
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
