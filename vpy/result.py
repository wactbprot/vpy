import datetime
import subprocess
import copy
import numpy as np
import matplotlib.pyplot as plt
#from .document import Document
from .analysis import Analysis
from .todo import ToDo
from .values import Values


class Result(Analysis):
    """Holds a deep copy of ``document``. Container for storing
    Results of analysis.
    """
    head_cell = {
        "cal": "{\\(p_{cal}\\)}",
        "ind": "{\\(p_{ind}\\)}",
        "ind_corr": "{\\(p_{ind} - p_{r}\\)}",
        "uncertTotal_rel": "{\\(U(k=2)\\)}",
        "uncertTotal_abs": "{\\(U(k=2)\\)}",
        "error":"{\\(e\\)}",
    }
    unit_cell = {
        "1": "",
        "mbar": "mbar",
        "%": "{\\(\\percent\\)}"
        }

    def __init__(self, doc):

        d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        init_dict = {"Date": [{
                    "Type": "generated",
                    "Value": d}]
             }

        self.ToDo = ToDo(doc)
        super().__init__(doc, init_dict)
        self.org = copy.deepcopy(doc)

    def flatten(self, l):
        """Flattens a list of lists.

        :param l: list of lists
        :type cal: list

        :returns: a list
        :rtype: list
        """
        return [item for sublist in l for item in sublist]

    def u_PTB_rel(self, p_list):
        return np.asarray([np.piecewise(p, [p <= 0.00027, p <= 0.003, p <= 0.0073, p <= 0.09, p <= 10, p <= 80,  80 < p],
                                        [0.0014, 0.001, 0.00092, 0.00086, 0.00075, 0.00019, 0.00014]).tolist() for p in p_list])

    def repeat_rel(self, p_list):
        return np.asarray([np.piecewise(p, [p <= 0.1, p <= 10, p > 10], [0.0008, 0.0003, 0.0001]).tolist() for p in p_list])

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

        :returns: array of arrays of indices
        :rtype: np.array
        """

        p_ind = ana.pick("Pressure", "ind", "mbar")
        p_cal = ana.pick("Pressure", "cal", "mbar")
        error = (p_ind - p_cal) / p_cal
        self.ToDo.make_average_index(p_cal, "mbar")
        idx = self.ToDo.average_index
        self.log.debug("average index: {}".format(idx))
        while True:
            r = []
            ref_mean = [None] * len(idx)
            ref_std = [None] * len(idx)
            s = [None] * len(idx)
            for i in range(len(idx)):
                s[i] = 1
                if i > 1:
                    s[i] = i
                if i > len(idx) - 3:
                    s[i] = len(idx) - 2
                # collect indices of neighbors
                ref_idx = self.flatten(idx[s[i] - 1: s[i] + 1])
                rr = []
                for j in range(len(idx[i])):
                    # indices of neighbors only
                    ref_idx0 = [a for a in ref_idx if a != idx[i][j]]
                    ref = np.take(error, ref_idx0).tolist()
                    ref_mean[i] = np.mean(ref)
                    ref_std[i] = np.std(ref)
                    # only accept indices if error[idx[i][j]] deviates either less than 5% or 10*sigma from neighbors
                    if abs(ref_mean[i] - error[idx[i][j]]) < max(0.05, 10 * ref_std[i]):
                        rr.append(idx[i][j])
                r.append(rr)
            self.log.debug("average index: {}".format(s))
            self.log.debug("average index: {}".format(idx))
            if self.io.plot == True:
                fig, ax = plt.subplots()
                x = [np.mean(np.take(p_cal, i).tolist()) for i in idx]
                ax.errorbar(x, ref_mean, ref_std, fmt='o', label="ref_mean")
                ax.semilogx(np.take(p_cal, self.flatten(idx)).tolist(), np.take(
                    error, self.flatten(idx)).tolist(), 'o', label="after refinement!")
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc=3)
                # plt.show()
            if idx == r:
                break
            idx = r
        self.average_index = idx

    def make_offset_uncert(self, ana):
        """Collects the pressure offsets of the main measurement only and
        calculates their standard deviation.

        :returns: standard uncertainty of offsets
        :rtype: float
        """
        p_off = ana.pick("Pressure", "offset", "mbar")
        p_off = self.flatten([np.take(p_off, i).tolist()
                              for i in self.average_index])
        mtime = ana.pick("Time", "Date", "date")
        mtime = self.flatten([np.take(mtime, i).tolist()
                              for i in self.average_index])
        occurrences = [[i, mtime.count(i)] for i in list(set(mtime))]
        max_occurrences = sorted(occurrences, key=lambda j: j[1])[-1][0]
        p_off_max_group = [p_off[i] for i in range(
            len(mtime)) if mtime[i] == max_occurrences]

        self.offset_uncert = np.std(p_off_max_group)

    def make_error_table(self, ana):

        cal = ana.pick("Pressure", "cal", "mbar")
        ind = ana.pick("Pressure", "ind", "mbar")
        error = 100 * (ind - cal) / cal

        av_idx = self.average_index
        n_avr = np.asarray([len(i) for i in av_idx])
        cal = np.asarray([np.mean(np.take(cal, i)) for i in av_idx])
        ind = np.asarray([np.mean(np.take(ind, i)) for i in av_idx])
        error = np.asarray([np.mean(np.take(error, i)) for i in av_idx])

        # digitizing error still missing
        u_ind_abs = np.sqrt((cal * self.repeat_rel(cal)) **
                            2 + (self.offset_uncert / np.sqrt(n_avr))**2)
        k2 = 2 * 100 * ind / cal * \
            np.sqrt((u_ind_abs / ind)**2 + self.u_PTB_rel(cal)**2)

        #format output
        cal_str = [f"{i:.4e}" for i in cal]
        ind_str = [f"{i:.4e}" for i in ind]
        error_str = [Values.round_uncertainty(1, error[i], k2[i]) for i in range(len(error))]
        k2_str = [f"{i:.2}" for i in k2]
 
        print(error_str)

        p_cal = {
            "Type": "cal",
            "Unit": "mbar",
            "Value": cal_str,
            "HeadCell": self.head_cell["cal"],
            "UnitCell": self.unit_cell["mbar"]
            }
        p_ind_corr = {
            "Type": "ind_corr",
            "Unit": "mbar",
            "Value": ind_str,
            "HeadCell": self.head_cell["ind_corr"],
            "UnitCell": self.unit_cell["mbar"]
            }
        e = {
            "Type": "relative",
            "Unit": "%",
            "Value": error_str,
            "HeadCell": self.head_cell["error"],
            "UnitCell": self.unit_cell["%"]
            }
        u  = {
            "Type": "uncertTotal_rel",
            "Unit": "%",
            "Value": k2_str,
            "HeadCell": self.head_cell["uncertTotal_rel"],
            "UnitCell": self.unit_cell["%"]
            }

        self.store_dict(quant="Table", d=p_cal, dest=None)
        self.store_dict(quant="Table", d=p_ind_corr, dest=None)
        self.store_dict(quant="Table", d=e, dest=None)
        self.store_dict(quant="Table", d=u, dest=None)

        self.log.info("Result error table written")


    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
