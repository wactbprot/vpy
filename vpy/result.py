import datetime
import subprocess
import copy
import numpy as np
import matplotlib.pyplot as plt
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

    def flatten(self, l):
        """Flattens a list of lists.

        :param l: list of lists
        :type cal: list

        :returns: a list
        :rtype: list
        """
        return [item for sublist in l for item in sublist] 


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
        error = (p_ind-p_cal)/p_cal
        self.ToDo.make_average_index(p_cal, "mbar")
        idx = self.ToDo.average_index
        self.log.debug("average index: {}".format(idx))
        # coarse filtering
        r = []
        for i in idx:
            rr = []
            for j in i:
                # only accept indicies with abs(error[j]) < 100%
                if abs(error[j]) < 1:
                    rr.append(j)
            r.append(rr)
        idx = r
        self.log.debug("average index: {}".format(idx))
        # refinement
        r = []
        ref_mean = [None]*len(idx)
        ref_std = [None]*len(idx)
        for i in range(len(idx)):
            s = 1
            if i > 1:
                s = i
            if i > len(idx) - 3:
                s = len(idx) - 2
            # collect neighbors
            ref = np.take(error, self.flatten(idx[s-1 : s+1])).tolist()
            ref_mean[i] = np.mean(ref)
            ref_std[i] = np.std(ref)
            rr = []
            for j in range(0, len(idx[i])):
                # only accept indicies if error[idx[i][j]] deviates either less than 1% or 3*sigma from neighbors
                if abs(ref_mean[i]-error[idx[i][j]]) < max(0.01, 3*ref_std[i]):
                    rr.append(idx[i][j])
            r.append(rr)
        idx = r
        self.log.debug("average index: {}".format(idx))
        if self.io.plot == True:
            fig, ax = plt.subplots()
            x = [np.mean(np.take(p_cal, i).tolist()) for i in idx]
            ax.errorbar(x, ref_mean, ref_std, fmt='o', label="ref_mean")
            ax.semilogx(np.take(p_cal, self.flatten(idx)).tolist(), np.take(error, self.flatten(idx)).tolist(),'o', label="after refinement!")
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, loc=3)
            plt.show()
        self.average_index = idx


    def make_error_table(self, res):
        p_cal = res.pick("Pressure", "cal", "mbar")
        av_idx = self.ToDo.make_average_index(p_cal, "mbar")


    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
