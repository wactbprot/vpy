import datetime
import time
import subprocess
import copy
import numpy as np
import matplotlib.pyplot as plt
import lmfit
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
    unit = {
        "mbar": "\\mbar",
        "Pa": "\\Pa"
        }
    gas = {
        "de": {
            "Ar": "Argon",
            "H2": "Wasserstoff",
            "N2": "Stickstoff",
            "Ne": "Neon"
            },
        "en": {
            "Ar": "argon",
            "H2": "hydrogen",
            "N2": "nitrogen",
            "Ne": "neon"
            }
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
        # coarse filtering
        idx = [[j for j in i if abs(error[j]) < 0.5] for i in idx]
        # fine filtering
        k = 0
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
                    # only accept indices if error[idx[i][j]] deviates either less than 5% or 5*sigma from neighbors
                    if abs(ref_mean[i] - error[idx[i][j]]) < max(0.05, 5* ref_std[i]):
                        rr.append(idx[i][j])
                r.append(rr)

            self.log.debug("average index: {}".format(s))
            self.log.debug("average index: {}".format(idx))
            
            k = k + 1
            if idx == r:
                break
            idx = r

        if self.io.make_plot == True:
            fig, ax = plt.subplots()
            x = [np.mean(np.take(p_cal, i).tolist()) for i in idx]
            ax.errorbar(x, ref_mean, ref_std, fmt='o', label="ref_mean")
            x = np.take(p_cal, self.flatten(idx)).tolist()
            y = np.take(error, self.flatten(idx)).tolist()               
            ax.semilogx(x, y, 'o', label="after refinement!")
            point_label = self.flatten(idx)
            for i in range(len(x)):
                plt.text(x[i], y[i], point_label[i], fontsize=8, horizontalalignment='center', verticalalignment='center')
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, loc=0)
            plt.title(str(k) + " mal durchlaufen")
            plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
            plt.ylabel(r"$e\;(\%)$")
            plt.savefig("reject_outliers.pdf")
            plt.clf()
            reject = []
            while True:
                r = input("Reject datapoint number: ")
                if r == "":
                    break
                reject.append(r)     
            print(idx)
            idx = [[j for j in i if not str(j) in reject] for i in idx]
            print(idx)

        self.average_index = idx


    def make_main_maesurement_index(self, ana):
        """Collects indices of the main measurement in average_index.

        :returns: list of indices
        :rtype: list
        """

        idx = self.flatten(self.average_index)
        mdate0 = ana.get_object("Type","measurement")["Value"]
        mdate = np.take(mdate0, idx).tolist()
        occurrences = [[i, mdate.count(i)] for i in list(set(mdate))]
        max_occurrence = sorted(occurrences, key=lambda j: j[1])[-1][0]
        idx = [i for i in idx if mdate0[i] == max_occurrence]

        self.main_maesurement_index = idx


    def make_pressure_range_index(self, ana):
        """Collects indices of measurements with the same conversion factor in r1.
        Collects indices of measurements within the same decade of p_cal in r2.
        Returns the one with smaller standard deviation in the low pressure range.

        :returns: list of lists of indices
        :rtype: list
        """

        cf = ana.get_object("Type","cf")["Value"]
        idx = self.flatten(self.average_index)

        r1 = {}
        for i in idx:
            for j in r1:
                if np.isclose(cf[i], cf[j], rtol=1.e-3) and np.isfinite(cf[j]):
                    r1[j].append(i)
                    break
            else: r1[i] = [i]
        r1 = list(r1.values())

        p_cal = ana.pick("Pressure", "cal", "mbar")
        p_off = ana.pick("Pressure", "offset", "mbar")
        p_cal_log10 = [int(i) for i in np.floor(np.log10(p_cal))]
        r2 = [[j for j in idx if p_cal_log10[j]==i and np.isfinite(cf[j])] for i in sorted(list(set(p_cal_log10)))]
        if len(r2[0]) < 5: r2 = [[*r2[0], *r2[1]], *r2[2:]]
        if len(r2[-1]) < 5: r2 = [*r2[:-2], [*r2[-2], *r2[-1]]]

        print("pressure ranges for offset stability")
        print(r1)
        print(r2)
        print([self.Val.round_to_sig_dig_array(np.take(p_cal, i), 2).tolist() for i in r1])
        print([self.Val.round_to_sig_dig_array(np.take(p_cal, i), 2).tolist() for i in r2])

        if np.std(np.take(p_off, r1[0])) < np.std(np.take(p_off, r2[0])): r = r1
        else: r = r2

        if self.io.make_plot == True:
            fig, ax = plt.subplots()
            x = np.take(p_cal, idx)
            y = np.take(p_off, idx)
            ax.semilogx(x, y, 'o')
            plt.title("offset stability")          
            plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
            plt.ylabel(r"$p_\mathrm{off}$ (mbar)")
            plt.savefig("offset_stability.pdf")
            plt.clf()

        self.pressure_range_index = r


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
            unc = np.std([p_off[j] for j in i])
            for j in i:
                offset_unc[j] = unc
        offset_unc = np.asarray([np.mean(np.take(offset_unc, i)) for i in av_idx])
        # should outliers by rejected? e.g. forgot to switch
        # measurement range for offset but switched for p_ind
        self.offset_uncertainty = min(offset_unc)
        
        # digitizing error still missing
        u_ind_abs = np.sqrt((cal * self.repeat_rel(cal))**2 + offset_unc**2)
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

        T_after = ana.pick("Temperature", "after", "C")
        T_room = ana.pick("Temperature", "room", "C")
        mdate = ana.get_object("Type","measurement")["Value"]

        mm_idx = self.main_maesurement_index

        mdate = np.take(mdate, mm_idx)[0]
        
        T_after = np.take(T_after, mm_idx)
        T_after_mean = np.mean(T_after)
        T_after_unc = np.std(T_after)
        T_after_mean_str = self.Val.round_to_uncertainty(T_after_mean, T_after_unc, 2)
        T_after_unc_str = self.Val.round_to_sig_dig(T_after_unc, 2)
        T_after_mean_K_str = self.Val.round_to_uncertainty(T_after_mean + 273.15, T_after_unc, 2)
        
        T_room = np.take(T_room, mm_idx)
        T_room_mean = np.mean(T_room)
        T_room_unc = np.std(T_room)
        T_room_mean_str = self.Val.round_to_uncertainty(T_room_mean, T_room_unc, 2)
        T_room_unc_str = self.Val.round_to_sig_dig(T_room_unc, 2)

        zero_stability_str = self.Val.round_to_sig_dig(self.offset_uncertainty, 2)

        target = self.org["Calibration"]["ToDo"]["Values"]["Pressure"]["Value"]
        target_unit = self.org["Calibration"]["ToDo"]["Values"]["Pressure"]["Unit"]
        target_unit = self.unit[target_unit]
        gas = self.org["Calibration"]["ToDo"]["Gas"]
        language = self.org["Calibration"]["Customer"]["Lang"]
        gas = self.gas[language][gas]

        form = {
            "GasTemperature": T_after_mean_str,
            "GasTemperatureUncertainty": T_after_unc_str,
            "MeasurementDate": mdate,
            "PressureRangeBegin": target[0],
            "PressureRangeEnd": target[-1],
            "PressureRangeUnit": target_unit,
            "GasSpecies": gas,
            "RoomTemperature": T_room_mean_str,
            "RoomTemperatureUncertainty": T_room_unc_str,
            "ZeroStability": zero_stability_str,
            "ZeroStabilityUnit": target_unit,
            "Evis": self.evis,
            "GasTemperatureEvis": T_after_mean_K_str,
            "GasTemperatureEvisUncertainty": T_after_unc_str
            }

        self.store_dict(quant="Formula", d=form, dest=None)

        self.log.info("Formula section written")


    def fit_thermal_transpiration(self):

        def model(p, a, b, c, d):
            return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)

        para_val, covariance = curve_fit(model, self.cal, self.error, bounds=([0, 0, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf]))
        residuals = model(self.cal, *para_val) - self.error
        para_unc = np.sqrt(np.diag(covariance))

        viscous_idx = [i for i in range(len(self.error)) if 0.8 < self.cal[i] < max(self.cal)]
        if len(viscous_idx) >= 4 and abs(np.mean(residuals[viscous_idx])) > 0.1:
            #if the deviation is high and there are enough data points in the viscous regime
            #take the mean of the smallest 3 values (excluding the one at highest pressure)
            self.evis = np.mean(sorted(self.error[viscous_idx])[0:3])
        else:
            self.evis = model(100, *para_val)

        if self.io.make_plot == True:
                fig, ax = plt.subplots()
                x = self.cal
                xdata = np.exp(np.linspace(np.log(min(x)), np.log(max(x)), 200))
                ax.errorbar(self.cal, self.error, self.k2, fmt='o', label="error")
                ax.semilogx(xdata, model(xdata, *para_val), '-', label="model")
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc=4)
                para_names = ["a", "b", "c", "d"]
                para_val_str = self.Val.round_to_uncertainty_array(para_val, para_unc, 2)
                para_unc_str = self.Val.round_to_sig_dig_array(para_unc, 2)
                text = "\n".join(["$" + para_names[i] + " = " + para_val_str[i] + "±" + para_unc_str[i] + "$" for i in range(len(para_names))])
                text = text + "\n\n" r"$e_\mathrm{vis}=" + self.Val.round_to_sig_dig(self.evis, 2) + "$"
                plt.title(r"model: $d + \frac{3.5}{a p^2 + b p + c \sqrt{p} + 1}$", y=1.05)          
                ax.annotate(text, xy=(0.6, 0.6), xycoords='figure fraction')
                plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
                plt.ylabel(r"$e\;(\%)$")
                plt.savefig("fit_thermal_transpiration.pdf")
                plt.clf()
        

    def fit_thermal_transpiration2(self):

        def model1(p, a, b, c, d):
            return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)
        
        model = lmfit.Model(model1)
        result = model.fit(self.error, p=self.cal, a=1, b=1, c=1, d=1)
        lmfit.report_fit(result.params, min_correl=0.5)
        
        para_val = [result.params[i].value for i in result.params]
        para_unc = [result.params[i].stderr for i in result.params]
        residuals = result.residual

        viscous_idx = [i for i in range(len(self.error)) if 0.8 < self.cal[i] < max(self.cal)]
        if len(viscous_idx) >= 4 and abs(np.mean(residuals[viscous_idx])) > 0.1:
            #if the deviation is high and there are enough data points in the viscous regime
            #take the mean of the smallest 3 values (excluding the one at highest pressure)
            self.evis = np.mean(sorted(self.error[viscous_idx])[0:3])
        else:
            self.evis = model1(100, *para_val)

        if self.io.make_plot == True:
                fig, ax = plt.subplots()
                x = self.cal
                xdata = np.exp(np.linspace(np.log(min(x)), np.log(max(x)), 200))
                ax.errorbar(self.cal, self.error, self.k2, fmt='o', label="error")
                ax.semilogx(xdata, model1(xdata, *para_val), '-', label="model")
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, loc=4)
                para_names = ["a", "b", "c", "d"]
                para_val_str = self.Val.round_to_uncertainty_array(para_val, para_unc, 2)
                para_unc_str = self.Val.round_to_sig_dig_array(para_unc, 2)
                text = "\n".join(["$" + para_names[i] + " = " + para_val_str[i] + "±" + para_unc_str[i] + "$" for i in range(len(para_names))])
                text = text + "\n\n" r"$e_\mathrm{vis}=" + self.Val.round_to_sig_dig(self.evis, 2) + "$"
                plt.title(r"model: $d + \frac{3.5}{a p^2 + b p + c \sqrt{p} + 1}$", y=1.05)          
                ax.annotate(text, xy=(0.6, 0.6), xycoords='figure fraction')
                plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
                plt.ylabel(r"$e\;(\%)$")
                plt.savefig("fit_thermal_transpiration.pdf")
                plt.clf()


    def make_sigma_formula(self):
        pass

    def make_evis_formula(self):
        pass

    def make_sens_table(self):
        pass
