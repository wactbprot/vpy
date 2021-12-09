import datetime
import time
import subprocess
import copy
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from ..document import Document
from ..analysis import Analysis
from ..todo import ToDo
from ..values import Values
from ..constants import Constants


class Display:

    def __init__(self, doc):
        self.Cons = Constants(doc)
        self.Val = Values(doc)
        self.main_title = "id: {}".format(doc.get("_id"))
        self.plt = plt

    def get_p_ind_mean(self, ana):
        return ana.pick("Pressure", "ind_mean", self.p_unit, dest="AuxValues")

    def get_error_mean(self, ana):
        return ana.pick("Error", "ind_mean", self.e_unit, dest="AuxValues")

    def get_u_mean(self, ana):
        return ana.pick("Uncertainty", "total_mean", self.e_unit, dest="AuxValues")

    def get_red_u_rep(self, ana):
        return ana.pick("Uncertainty", "red_u_rep","1", dest="AuxValues")

    def get_red_u_std(self, ana):
        return ana.pick("Uncertainty", "red_u_std","1", dest="AuxValues")

    def get_red_u_dev(self, ana):
        return ana.pick("Uncertainty", "red_u_dev","1", dest="AuxValues")

    def get_red_u_tot(self, ana):
        return ana.pick("Uncertainty", "red_u_tot","1", dest="AuxValues")

    def get_red_u_off(self, ana):
        return ana.pick("Uncertainty", "red_u_off","1", dest="AuxValues")

    def get_red_p_cal(self, ana):
        return ana.pick("Pressure", "red_cal", self.p_unit, dest="AuxValues")

    def get_red_err(self, ana):
        return ana.pick("Error", "red_ind", self.e_unit, dest="AuxValues")

    def add_point_no(self, x, y):
        for i, v in enumerate(x):
            self.plt.text(v, y[i], i, rotation=45.)

    def tlg(self):
        self.plt.title(self.main_title)
        self.plt.legend()
        self.plt.grid()

    def show(self):
        self.tlg()
        self.plt.show()


    def plot(self, x, y, label="data", show=True, linestyle= "None", marker="o"):
        self.plt.plot(x, y,
                      marker = marker,
                      linestyle = linestyle,
                      markersize = self.norm_markersize,
                      label=label)
        if show:
            self.show()

    def xlog_plot(self, x, y, label="data", show=True, linestyle= "None", marker="o"):
        self.plt.xscale('symlog', linthresh=1e-12)
        self.plot(x, y, linestyle=linestyle, marker=marker, label=label, show=show)

    def check_outlier_err(self, ana, label="measurement", show=True):
        x = self.get_p_cal(ana)
        y = self.get_err(ana)
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("e in {}".format(self.e_unit))
        self.xlog_plot(x , y, label=label, show=show)

    def check_outlier_sens(self, ana, label="measurement", show=True):
        x = self.get_p_cal(ana)
        y = self.get_sens(ana)
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("S in {}".format(self.s_unit))
        self.xlog_plot(x , y, label=label, show=show)

    def check_outlier_sigma(self, ana, label="measurement", p_unit="Pa", show=True):
        x = self.get_p_cal(ana)
        y = self.get_sigma(ana)
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(p_unit))
        self.plt.ylabel("$\sigma_{eff}$ ")
        self.plot(x , y, label=label, show=show)

    def plot_uncert(self, ana, show=True):
        self.plt.cla()
        x = self.get_red_p_cal(ana)

        u_rep = self.get_red_u_rep(ana)
        u_std = self.get_red_u_std(ana)
        u_dev = self.get_red_u_dev(ana)
        u_tot = self.get_red_u_tot(ana)
        u_off = self.get_red_u_off(ana)

        y = np.vstack([u_rep, u_off,])
        labels =      ["u_rep","u_off",]

        self.plt.subplot(211)
        self.plt.xscale('symlog', linthresh=1e-12)
        self.plt.stackplot(x,u_tot, labels=["u_total (sq. sum)"], alpha=1)
        self.plt.stackplot(x,u_dev, labels=["u_device (sq. sum) "], alpha=1)
        self.plt.stackplot(x,y, labels=labels, alpha=0.8)
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("u(k=1) in {}".format(self.e_unit))
        self.tlg()

        self.plt.subplot(212)
        y = np.vstack([u_std, u_dev,])
        labels = ["u_std","u_dev",]

        self.plt.xscale('symlog', linthresh=1e-12)
        self.plt.stackplot(x, u_tot, labels=["u_total (sq. sum)"], alpha=1)
        self.plt.stackplot(x,y, labels=labels, alpha=0.8)

        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("u(k=1) in {}".format(self.e_unit))

        self.show()

    def plot_mean(self, ana, show=True):
        self.plt.cla()
        x = self.get_red_p_cal(ana)
        y = self.get_red_err(ana)
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("e in {}".format(self.e_unit))
        self.xlog_plot(x , y, label="red. measurement", show=False)
        x = self.get_p_ind_mean(ana)
        y = self.get_error_mean(ana)
        u = self.get_u_mean(ana)
        self.plt.errorbar(x, y, yerr=u, label="certificate")
        if show:
            self.show()
