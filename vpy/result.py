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
        """Takes the list of indices of measurement points belonging to a
        certain target pressure and rejects outliers by comparing each
        measurement value to the mean value of the neighbors (without the
        point itself).
        remarks: using the standard deviation of the neighbors is unsatisfactory
        because one may end up with a small value by chance. Probably it is
        better to use a threshold that is decreasing with increasing pressure
        values. Another problem is that iterating over empty lists aborts the
        program.

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
        while True:
            r = []
            ref_mean = [None]*len(idx)
            ref_std = [None]*len(idx)
            s = [None]*len(idx)
            for i in range(len(idx)):
                s[i] = 1
                if i > 1:
                    s[i] = i
                if i > len(idx) - 3:
                    s[i] = len(idx) - 2
                # collect indices of neighbors
                ref_idx = self.flatten(idx[s[i]-1 : s[i]+1])
                rr = []
                for j in range(len(idx[i])):
                    # indices of neighbors only
                    ref_idx0 = [a for a in ref_idx if a != idx[i][j]]
                    ref = np.take(error, ref_idx0).tolist() 
                    ref_mean[i] = np.mean(ref)
                    ref_std[i] = np.std(ref)
                    # only accept indices if error[idx[i][j]] deviates either less than 1% or 3*sigma from neighbors
                    if abs(ref_mean[i]-error[idx[i][j]]) < max(0.05, 100*ref_std[i]):
                        rr.append(idx[i][j])
                    else:
                        print(abs(ref_mean[i]-error[idx[i][j]]))
                        print(100*ref_std[i])
                r.append(rr)

            self.log.debug("average index: {}".format(s))
            self.log.debug("average index: {}".format(idx))
            if self.io.plot == True:
                fig, ax = plt.subplots()
                x = [np.mean(np.take(p_cal, i).tolist()) for i in idx]
                ax.errorbar(x, ref_mean, ref_std, fmt='o', label="ref_mean")
                ax.semilogx(np.take(p_cal, self.flatten(idx)).tolist(), np.take(error, self.flatten(idx)).tolist(),'o', label="after refinement!")
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc=3)
                plt.show()
            if idx == r:
                break
            idx = r
        self.average_index = idx

    def offset_uncert(self, ana):
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

        p_off = ana.pick("Pressure", "offset", "mbar")

        pass


    def make_error_table(self, res):
        p_cal = res.pick("Pressure", "cal", "mbar")
        av_idx = self.ToDo.make_average_index(p_cal, "mbar")


    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
