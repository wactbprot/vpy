import numpy as np
import sympy as sym
from ..device.device import Device
from ..constants import Constants

class Rsg(Device):

    def __init__(self, doc, dev):
        self.Const = Constants(doc)
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
