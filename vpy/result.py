import datetime
import subprocess
import copy
import numpy as np
from .document import Document
from .todo import ToDo

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

        self.ToDo = ToDo(doc)
        super().__init__(o)
        self.org = doc

    def reject_outliers_index(self, ana):
        """Generates and returns a numpy array containing
        the indices of measurement points which belong to a
        certain target pressure.

        :param cal: np array of values to group
        :type cal: np.array

        :param unit: unit of cal
        :type unit: str

        :returns: array of arrays of indices
        :rtype: np.array
        """

        p_ind = ana.pick("Pressure", "ind", "mbar")
        p_cal = ana.pick("Pressure", "cal", "mbar")
        idx = self.ToDo.make_average_index(p_cal, "mbar")


    def make_error_table(self, res):
        p_cal = res.pick("Pressure", "cal", "mbar")
        av_idx = self.ToDo.make_average_index(p_cal, "mbar")


    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
