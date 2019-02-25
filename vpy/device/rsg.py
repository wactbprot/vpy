import numpy as np
import sympy as sym
from ..device.device import Device

class Rsg(Device):

    def __init__(self, doc, dev):
        super().__init__(doc, dev)

    def get_name(self):
        return self.doc['Name']
