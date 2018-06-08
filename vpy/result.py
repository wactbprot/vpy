import datetime
import subprocess
import copy
import numpy as np
from .document import Document

class Result(Document):
    """Holds a deep copy of ``document``. Container for storing
    Results of analysis.
    """

    def __init__(self, doc):
        doc = copy.deepcopy(doc)
        d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        o = {"Date": [{
            "Type": "generated",
                    "Value": d}],
             "Values": {}
             }

        super().__init__(o)
        self.org = doc

    def make_error_table(self, res^):
        p_cal = res.pick("Pressure", "cal", "mbar")
        av_idx = self.ToDo.get_average_index(p_cal, "mbar")
        

    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
