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


class Display:

    def __init__(self, doc):
        self.doc = doc
        self.Cons = Constants(doc)
        self.Val = Values(doc)
     

    def SE2_CDG_offset_abs(self):

        idx = self.doc['Calibration']['Analysis']['AuxValues']['AverageIndexFlat']
        pr_idx = self.doc['Calibration']['Analysis']['AuxValues']['PressureRangeIndex']

        pressure = Document(self.doc['Calibration']['Analysis']['Values']['Pressure'])

        pcal0, pcal0_unit = pressure.get_value_and_unit('cal')
        pcal0 = pcal0 * self.Cons.get_conv(pcal0_unit, "Pa")

        poff0, poff0_unit = pressure.get_value_and_unit('offset')
        poff0 = poff0 * self.Cons.get_conv(poff0_unit, "Pa")        

        uncertainty = Document(self.doc['Calibration']['Analysis']['Values']['Uncertainty'])
        offset_unc, offset_unc_unit = uncertainty.get_value_and_unit('offset_abs')
        offset_unc = offset_unc * self.Cons.get_conv(offset_unc_unit, "Pa")  

        for i in pr_idx:
            i_idx = np.intersect1d(idx,i)
            x = np.take(pcal0, i_idx)
            y = np.take(poff0, i_idx)
            y_err = np.take(offset_unc, i_idx)
            plt.errorbar(x, y, y_err, fmt='o')
        plt.semilogx(x, y, 'o')
        plt.title("offset stability")
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')          
        plt.xlabel(r"$p_\mathrm{cal}$ (Pa)")
        plt.ylabel(r"$p_\mathrm{off}$ (Pa)")
        plt.rcParams['figure.figsize']=8,6
        return plt        


    def SE2_CDG_offset_rel(self):

        idx = self.doc['Calibration']['Analysis']['AuxValues']['AverageIndexFlat']
        pr_idx = self.doc['Calibration']['Analysis']['AuxValues']['PressureRangeIndex']

        pressure = Document(self.doc['Calibration']['Analysis']['Values']['Pressure'])

        pcal0, pcal0_unit = pressure.get_value_and_unit('cal')
        pcal0 = pcal0 * self.Cons.get_conv(pcal0_unit, "Pa")

        poff0, poff0_unit = pressure.get_value_and_unit('offset')
        poff0 = poff0 * self.Cons.get_conv(poff0_unit, "Pa")        

        uncertainty = Document(self.doc['Calibration']['Analysis']['Values']['Uncertainty'])
        offset_unc, offset_unc_unit = uncertainty.get_value_and_unit('offset_abs')
        offset_unc = offset_unc * self.Cons.get_conv(offset_unc_unit, "Pa")  

        for i in pr_idx:
            i_idx = np.intersect1d(idx,i)
            x = np.take(pcal0, i_idx)
            y = np.take(poff0 / pcal0 * 100, i_idx)
            y_err = np.take(offset_unc, i_idx) / np.take(pcal0, i_idx) * 100
            plt.errorbar(x, y, y_err, fmt='o')
        plt.semilogx(x, y, 'o')
        plt.title("offset stability")
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')                
        plt.xlabel(r"$p_\mathrm{cal}$ (Pa)")
        plt.ylabel(r"$p_\mathrm{off}\,/\,p_\mathrm{cal}$ (%)")
        plt.rcParams['figure.figsize']=8,6
        return plt


    def SE2_CDG_error_plot(self):

        def model(p, a, b, c, d):
            return d + 3.5 / (a * p**2 + b * p + c * np.sqrt(p) + 1)

        pressure = Document(self.doc['Calibration']['Analysis']['Values']['Pressure'])           
        error = Document(self.doc['Calibration']['Analysis']['Values']['Error'])
        pcal0 = pressure.get_value('cal', 'Pa')
        e0 = error.get_value('ind', '1')

        idx = (abs(e0) > 0.5)
        if len(idx) > 0:
            e0[idx] = np.nan

        result = Document(self.doc['Calibration']['Result']['Table'])
        pcal, pcal_unit = result.get_value_and_unit('cal')
        pcal = np.asarray(pcal, dtype=float)
        pcal = pcal * self.Cons.get_conv(pcal_unit, "Pa")
        error, error_unit = result.get_value_and_unit('ind')
        error = np.asarray(error, dtype=float)
        error = error * self.Cons.get_conv(error_unit, "%")
        unc, unc_unit = result.get_value_and_unit('uncert_total_rel')
        unc = np.asarray(unc, dtype=float)
        unc = unc * self.Cons.get_conv(unc_unit, "%")

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

        x = pcal
        xdata = np.exp(np.linspace(np.log(min(x)), np.log(max(x)), 200))
        plt.errorbar(pcal, error, unc, fmt='o', label="error")
        plt.semilogx(xdata, model(xdata, *para_val), '-', label="model")
        plt.legend(loc=9, bbox_to_anchor=(0.95, 1.1))
        para_names = ["a", "b", "c", "d"]
        para_val_str = self.Val.round_to_uncertainty_array(para_val, para_unc, 2)
        para_unc_str = self.Val.round_to_sig_dig_array(para_unc, 2)
        text = "\n".join(["$" + para_names[i] + " = " + para_val_str[i] + "±" + para_unc_str[i] + "$" for i in range(len(para_names))])
        text = text + "\n\n" r"$e_\mathrm{vis}=" + self.Val.round_to_sig_dig(evis, 2) + "$"
        plt.title(r"model: $d + \frac{3.5}{a p^2 + b p + c \sqrt{p} + 1}$", y=1.05, x=0.25)
        plt.annotate(text, xy=(0.6, 0.6), xycoords='figure fraction')
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')
        plt.xlabel(r"$p_\mathrm{cal}$ (Pa)")
        plt.ylabel(r"$e\;(\%)$")
        plt.rcParams['figure.figsize']=8,6
        return plt


    def SE2_CDG_error_reject(self):
        """Reject outliers by several filtering algorithms.
        """

        idx = self.doc['Calibration']['Analysis']['AuxValues']['AverageIndexFlat']
        try:
            r_idx = self.doc['Calibration']['Analysis']['AuxValues']['RejectIndex']
        except:
            r_idx = []
        u_idx = np.asarray(np.union1d(idx, r_idx), dtype=int)

        pressure = Document(self.doc['Calibration']['Analysis']['Values']['Pressure'])
        error = Document(self.doc['Calibration']['Analysis']['Values']['Error'])

        pcal0, pcal0_unit = pressure.get_value_and_unit('cal')
        pcal0 = pcal0 * self.Cons.get_conv(pcal0_unit, "Pa")

        e0, e0_unit = error.get_value_and_unit('ind')
        e0 = e0 * self.Cons.get_conv(e0_unit, "%")

        result = Document(self.doc['Calibration']['Result']['Table'])
        pcal, pcal_unit = result.get_value_and_unit('cal')
        pcal = np.asarray(pcal, dtype=float)
        pcal = pcal * self.Cons.get_conv(pcal_unit, "Pa")
        error, error_unit = result.get_value_and_unit('ind')
        error = np.asarray(error, dtype=float)
        error = error * self.Cons.get_conv(error_unit, "%")
        unc, unc_unit = result.get_value_and_unit('uncert_total_rel')
        unc = np.asarray(unc, dtype=float)
        unc = unc * self.Cons.get_conv(unc_unit, "%")

        x = np.take(pcal0, idx)
        y = np.take(e0, idx)
        plt.semilogx(x, y, 'o', label="accept")

        plt.errorbar(pcal, error, unc, fmt='o', label="result")

        x = np.take(pcal0, r_idx)
        y = np.take(e0, r_idx)
        plt.semilogx(x, y, 'o', label="reject")

        x = np.take(pcal0, u_idx)
        y = np.take(e0, u_idx)
        for i in range(len(u_idx)):
            plt.text(x[i], y[i], u_idx[i], fontsize=10, horizontalalignment='center', verticalalignment='center')

        plt.legend(loc=0)
        plt.title("reject outliers")
        plt.grid(True, which='both', linestyle='-', linewidth=0.1, color='0.85')
        plt.xlabel(r"$p_\mathrm{cal}$ (?)")
        plt.ylabel(r"$e\;(\%)$")
        plt.rcParams['figure.figsize']=8,6
        return plt