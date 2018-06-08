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
        flatten = lambda l: [item for sublist in l for item in sublist]        

        p_ind = ana.pick("Pressure", "ind", "mbar")
        p_cal = ana.pick("Pressure", "cal", "mbar")
        error = (p_ind-p_cal)/p_cal
        self.ToDo.make_average_index(p_cal, "mbar")
        idx = self.ToDo.average_index
        print(idx)
        # coarse filtering
        r = []
        for i in idx:
            rr = []
            for j in i:
                # only accept indicies with error[j] < 100%
                if abs(error[j]) < 1:
                    rr.append(j)
            r.append(rr)
        idx = r
        print(idx)
        # refinement
        r = []
        for i in range(0, len(idx)):
            s = 1
            if i > 1:
                s = i
            if i > len(idx) - 3:
                s = len(idx) - 2
            # collect neighbors
            ref = np.take(error, flatten(idx[s-1 : s+1])).tolist()
            rr = []
            for j in range(0, len(idx[i])):
                # only accept indicies if error[idx[i][j]] deviates less than 3*sigma from neighbors
                if abs(np.mean(ref)-error[idx[i][j]]) < 3*np.std(ref):
                    rr.append(idx[i][j])
            r.append(rr)
        idx = r
        print(idx)
        self.average_final_index = idx


    def make_error_table(self, res):
        p_cal = res.pick("Pressure", "cal", "mbar")
        av_idx = self.ToDo.make_average_index(p_cal, "mbar")


    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
