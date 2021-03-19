import numpy as np
from ..display.display import Display

class CE3(Display):
    p_unit = "Pa"
    e_unit = "1"
    s_unit = "1"
    norm_markersize = 10


    def __init__(self, doc):
        super().__init__(doc)

    def get_p_cal(self, ana):
        return ana.pick("Pressure", "cal", self.p_unit)

    def get_err(self, ana):
        return ana.pick("Error", "ind", self.e_unit)
