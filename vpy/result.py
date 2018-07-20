import datetime
import subprocess
import copy
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
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
        "%": "{\\(\\si{\\percent}\\)}"
        }

    def __init__(self, doc):

        d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        init_dict = {"Date": [{
                    "Type": "generated",
                    "Value": d}]
             }

        self.ToDo = ToDo(doc)
        self.Val = Values(doc)
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


    def gatherby_idx(self, l, compare_function):
        groups = {}
        for i in range(len(l)):
            for j in groups:
                if compare_function(l[i], l[j]):
                    groups[j].append(i)
                    break
            else: groups[i] = [i]
        return list(groups.values())


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
            if self.io.make_plot == True:
                fig, ax = plt.subplots()
                x = [np.mean(np.take(p_cal, i).tolist()) for i in idx]
                ax.errorbar(x, ref_mean, ref_std, fmt='o', label="ref_mean")
                ax.semilogx(np.take(p_cal, self.flatten(idx)).tolist(), np.take(
                    error, self.flatten(idx)).tolist(), 'o', label="after refinement!")
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc=4)
                plt.savefig("reject_outliers.pdf")
                plt.clf()
            if idx == r:
                break
            idx = r
        self.average_index = idx


    def make_main_maesurement_index(self, ana):
        """Collects indices of the main measurement in average_index.

        :returns: list of indices
        :rtype: list
        """

        idx = self.flatten(self.average_index)
        mtime0 = ana.pick("Time", "Date", "date")
        mtime = np.take(mtime0, idx).tolist()
        occurrences = [[i, mtime.count(i)] for i in list(set(mtime))]
        max_occurrence = sorted(occurrences, key=lambda j: j[1])[-1][0]
        idx = [i for i in idx if mtime0[i] == max_occurrence]

        self.main_maesurement_index = idx


    def make_pressure_range_index(self, ana):
        """Collects indices of measurements with the same conversion factor.

        :returns: list of lists of indices
        :rtype: list
        """

        cf = ana.pick("Pressure", "cf", "")
        idx = self.flatten(self.average_index)
        r = {}

        for i in idx:
            for j in r:
                if np.isclose(cf[i], cf[j], rtol=1.e-3):
                    r[j].append(i)
                    break
            else: r[i] = [i]

        self.pressure_range_index = list(r.values())


    def make_error_table(self, ana):

        cal = ana.pick("Pressure", "cal", "mbar")
        ind = ana.pick("Pressure", "ind", "mbar")
        error = 100 * (ind - cal) / cal
        
        p_off = ana.pick("Pressure", "offset", "mbar")

        av_idx = self.average_index
        n_avr = np.asarray([len(i) for i in av_idx])
        cal = self.cal = np.asarray([np.mean(np.take(cal, i)) for i in av_idx])
        ind = self.ind = np.asarray([np.mean(np.take(ind, i)) for i in av_idx])
        error = self.error = np.asarray([np.mean(np.take(error, i)) for i in av_idx])

        mm_idx = self.main_maesurement_index
        pr_idx = self.pressure_range_index
        offset_unc = [None] * len(p_off)
        for i in pr_idx:
            print("hello")
            print(av_idx)
            print(pr_idx)
            print(mm_idx)
            print([p_off[j] for j in i if j in mm_idx and not np.isnan(p_off[j])])
            unc = np.std([p_off[j] for j in i if j in mm_idx and np.isfinite(p_off[j])])
            for j in i:
                offset_unc[j] = unc
        offset_unc = np.asarray([np.mean(np.take(offset_unc, i)) for i in av_idx])
        # should outliers by rejected? e.g. forgot to switch
        # measurement range for offset but switched for p_ind
        self.offset_uncertainty = min(offset_unc)
        print("bite me:)")
        print(offset_unc)
        
        # digitizing error still missing
        u_ind_abs = np.sqrt((cal * self.repeat_rel(cal))**2 + (offset_unc / np.sqrt(n_avr))**2)
        k2 = self.k2 = 2 * 100 * ind / cal * np.sqrt((u_ind_abs / ind)**2 + self.u_PTB_rel(cal)**2)

        #format output
        cal_str = [f"{i:.4e}" for i in cal]
        ind_str = [f"{i:.4e}" for i in ind]
        error_str = self.Val.round_to_uncertainty_array(error, k2, 2)
        k2_str = self.Val.round_to_sig_dig_array(k2, 2)
 
        # print("error_table")
        # print(cal_str)
        # print(ind_str)
        # print(error_str)
        # print(k2_str)

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


    def make_formula_section(self, ana):

        T_before = ana.pick("Temperature", "before", "C")
        T_room = ana.pick("Temperature", "room", "C")

        mm_idx = self.main_maesurement_index
        
        T_before = np.take(T_before, mm_idx)
        T_before_mean = np.mean(T_before)
        T_before_unc = np.std(T_before)
        T_before_mean_str = self.Val.round_to_uncertainty(T_before_mean, T_before_unc, 2)
        T_before_unc_str = self.Val.round_to_sig_dig(T_before_unc, 2)
        
        T_room = np.take(T_room, mm_idx)
        T_room_mean = np.mean(T_room)
        T_room_unc = np.std(T_room)
        T_room_mean_str = self.Val.round_to_uncertainty(T_room_mean, T_room_unc, 2)
        T_room_unc_str = self.Val.round_to_sig_dig(T_room_unc, 2)

        zero_stability_str = self.Val.round_to_sig_dig(self.offset_uncertainty, 2)

        form = {
            "GasTemperature": T_before_mean_str,
            "GasTemperatureUncertainty": T_before_unc_str,
            "GasTemperatureUnit": "\\si{\\degreeCelsius}",
            "RoomTemperature": T_room_mean_str,
            "RoomTemperatureUncertainty": T_room_unc_str,
            "RoomTemperatureUnit": "\\si{\\degreeCelsius}",
            "ZeroStability": zero_stability_str,
            "ZeroStabilityUnit": "mbar",
            "Evis": "0.1",
            "EvisUnit": "\\si{\\percent}",
            "GasTemperatureEvis": "296.01",
            "GasTemperatureEvisUncertainty": "0.28",
            "GasTemperatureEvisUnit": "K"
            }

        self.store_dict(quant="Formula", d=form, dest=None)

        self.log.info("Formula section written")


    def fit_thermal_transpiration(self):

        def model(p, a, b, c, d):
            return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)

        para_val, covariance = curve_fit(model, self.cal, self.ind)
        para_unc = np.sqrt(np.diag(covariance))

        if self.io.make_plot == True:
                fig, ax = plt.subplots()
                x = self.cal
                xdata = np.exp(np.linspace(np.log(min(x)), np.log(max(x)), 200))
                ax.errorbar(self.cal, self.ind, self.k2, fmt='o', label="error")
                ax.semilogx(xdata, model(xdata, *para_val), '-', label="model")
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc=4)
                para_names = ["a", "b", "c", "d"]
                para_val_str = self.Val.round_to_uncertainty_array(para_val, para_unc, 2)
                para_unc_str = self.Val.round_to_sig_dig_array(para_unc, 2)
                text = "\n".join([para_names[i] + " = " + para_val_str[i] + "±" + para_unc_str[i] for i in range(len(para_names))])
                plt.title("d + 3.5 / (a p^2 + b p + c sqrt(p) + 1)")          
                ax.annotate(text, xy=(0.6, 0.7), xycoords='figure fraction')
                plt.savefig("fit_thermal_transpiration.pdf")
                plt.clf()
        

    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
