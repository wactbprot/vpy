import datetime
import time
import subprocess
import copy
import numpy as np
from .document import Document
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from .analysis import Analysis
from .todo import ToDo
from .values import Values
from .constants import Constants


class Display(Document):
    """Holds a deep copy of ``document``.
    """

    def __init__(self, doc):

        self.Val = Values(doc)
        self.Cons = Constants(doc)
        super().__init__(None)
        self.org = copy.deepcopy(doc)


    def SE2_CDG_offset_abs(self):

        try:
            idx = self.org['Calibration']['Result']['AuxValues']['AverageIndexFlat']

            measurement = Document(self.org['Calibration']['Measurement']['Values'])
            pcal0, pcal0_unit = measurement.get_value_and_unit('p_cal')
            pcal0 = pcal0 * self.Cons.get_conv(pcal0_unit, "mbar")
            poff0, poff0_unit = measurement.get_value_and_unit('offset')
            poff0 = poff0 * self.Cons.get_conv(poff0_unit, "mbar")       

        except:
            print("error")

        plt.clf()
        fig, ax = plt.subplots()
        x = np.take(pcal0, idx)
        y = np.take(poff0, idx)
        y_err = np.take(offset_unc, idx) #<----
        ax.errorbar(x, y, y_err, fmt='o')
        ax.semilogx(x, y, 'o')
        plt.title("offset stability")
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')          
        plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
        plt.ylabel(r"$p_\mathrm{off}$ (mbar)")
        plt.savefig("offset_stability_abs2_" + str(self.org["Calibration"]["Certificate"]) + ".pdf")
        plt.rcParams['figure.figsize']=8,6
        return plt


    def SE2_CDG_error_plot(self):

        def model(p, a, b, c, d):
            return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)

        try:
            measurement = Document(self.org['Calibration']['Measurement']['Values'])
            print(measurement.doc)
            pcal0, pcal0_unit = measurement.get_value_and_unit('p_cal')
            pcal0 = pcal0 * self.Cons.get_conv(pcal0_unit, "mbar")
            error0 = measurement.get_value('ind', '')
            idx = (abs(error0) > 50)
            if len(idx) > 0:
                error0[idx] = np.nan

            result = Document(self.org['Calibration']['Result']['Table'])
            pcal, pcal_unit = result.get_value_and_unit('cal')
            pcal = np.asarray(pcal, dtype=float)
            pcal = pcal * self.Cons.get_conv(pcal_unit, "mbar")
            error, error_unit = result.get_value_and_unit('relative')
            error = np.asarray(error, dtype=float)
            error = error * self.Cons.get_conv(error_unit, "%")
            unc, unc_unit = result.get_value_and_unit('uncertTotal_rel')
            unc = np.asarray(unc, dtype=float)
            unc = unc * self.Cons.get_conv(unc_unit, "%")            

        except:
            print("error")

        para_val, covariance = curve_fit(model, pcal, error, bounds=([0, 0, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf]), maxfev=1000)
        residuals = model(pcal, *para_val) - error
        para_unc = np.sqrt(np.diag(covariance))

        viscous_idx = [i for i in range(len(error)) if 0.8 < pcal[i] < max(pcal)]
        if len(viscous_idx) >= 4 and abs(np.mean(residuals[viscous_idx])) > 0.1:
            #if the deviation is high and there are enough data points in the viscous regime
            #take the mean of the smallest 3 values (excluding the one at highest pressure)
            evis = np.mean(sorted(error[viscous_idx])[0:3])
        else:
            evis = model(100, *para_val)

        plt.clf()
        fig, ax = plt.subplots()
        x = pcal
        xdata = np.exp(np.linspace(np.log(min(x)), np.log(max(x)), 200))
        ax.errorbar(pcal, error, unc, fmt='o', label="error")
        ax.semilogx(xdata, model(xdata, *para_val), '-', label="model")
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc=9, bbox_to_anchor=(0.95, 1.1))
        para_names = ["a", "b", "c", "d"]
        para_val_str = self.Val.round_to_uncertainty_array(para_val, para_unc, 2)
        para_unc_str = self.Val.round_to_sig_dig_array(para_unc, 2)
        text = "\n".join(["$" + para_names[i] + " = " + para_val_str[i] + "±" + para_unc_str[i] + "$" for i in range(len(para_names))])
        text = text + "\n\n" r"$e_\mathrm{vis}=" + self.Val.round_to_sig_dig(evis, 2) + "$"
        plt.title(r"model: $d + \frac{3.5}{a p^2 + b p + c \sqrt{p} + 1}$", y=1.05, x=0.25)
        ax.annotate(text, xy=(0.6, 0.6), xycoords='figure fraction')
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')
        plt.xlabel(r"$p_\mathrm{cal}$ (mbar)")
        plt.ylabel(r"$e\;(\%)$")
        plt.rcParams['figure.figsize']=8,6
        return plt


    def show(self):
        values = Document(self.org.get('Calibration').get('Measurement').get('Values'))
        values.get_value('T_room', 'C')
        T_val, T_unit = values.get_value_and_unit('T_room')
        print("**here!**")
        print(values.get_value('T_room', 'C'))
        #print(values.get_values('T_room', 'K'))
        print(T_val, T_unit)
        print(values.doc)
        print(values.get_value('ind', 'K'))
        print(self.org.get('Calibration').get('Result').get('Table'))