import numpy as np
from ..display.display import Display

class CE3(Display):
    p_unit = "Pa"
    e_unit = "1"
    s_unit = "1/Pa"
    norm_markersize = 10


    def __init__(self, doc):
        super().__init__(doc)

    def get_p_cal(self, ana):
        return ana.pick("Pressure", "cal", self.p_unit)

    def get_err(self, ana):
        return ana.pick("Error", "ind", self.e_unit)

    def get_sens(self, ana):
        return ana.pick("Sensitivity", "gauge", self.s_unit)

    def get_sens_mean(self, ana):
        return ana.pick("Sensitivity", "gauge_mean", self.s_unit, dest="AuxValues")

    def get_error_mean(self, ana):
        return ana.pick("Error", "ind_mean", self.e_unit, dest="AuxValues")

    def get_p_cal_mean(self, ana):
        return ana.pick("Pressure", "cal_mean", self.p_unit, dest="AuxValues")

    def get_red_sens(self, ana):
        return ana.pick("Sensitivity", "red_gauge", self.s_unit, dest="AuxValues")

    def get_red_error(self, ana):
        return ana.pick("Error", "red_ind", self.e_unit, dest="AuxValues")

    def plot_mean(self, ana, show=True):
        self.plt.cla()
        x = self.get_red_p_cal(ana)
        self.plt.xlabel("p in {}".format(self.p_unit))

        if ana.analysis_type == "sens":
            y = self.get_red_sens(ana)
            self.plt.ylabel("S in {}".format(self.s_unit))
        else:
            y = self.get_red_error(ana)
            self.plt.ylabel("e in {}".format(self.e_unit))


        self.xlog_plot(x , y, label="red. measurement", show=False)
        x = self.get_p_cal_mean(ana)

        if ana.analysis_type == "sens":
            y = self.get_sens_mean(ana)
        else:
            y = self.get_error_mean(ana)
        u = self.get_u_mean(ana)

        self.plt.errorbar(x, y, yerr=u, label="certificate")
        if show:
            self.show()
