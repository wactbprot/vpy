import datetime
import subprocess
import copy
import numpy as np
from .document import Document

class Results(Document):
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

    def make_error_table(self):
        pass

    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass

