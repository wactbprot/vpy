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
        self.plt.xscale('symlog', linthreshx=1e-12)
        self.plot(x, y, linestyle=linestyle, marker=marker, label=label, show=show)

    def check_outlier_err(self, ana, label="measurement", show=True):
        x = self.get_p_cal(ana)
        y = self.get_err(ana)
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("e in {}".format(self.e_unit))
        self.xlog_plot(x , y, label=label, show=show)

    def check_outlier_sigma(self, ana, label="measurement", p_unit="Pa", show=True):
        x = self.get_p_cal(ana)
        y = self.get_sigma(ana)
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(p_unit))
        self.plt.ylabel("$\sigma_{eff}$ ")
        self.plot(x , y, label=label, show=show)
