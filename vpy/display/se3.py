import numpy as np
from ..display.display import Display

class SE3(Display):
    p_unit = "Pa"
    e_unit = "1"
    s_unit = "1"
    norm_markersize = 10


    def __init__(self, doc):
        super().__init__(doc)


    def get_average_index_flat(self, ana):
        return ana.doc.get("AuxValues").get("AverageIndexFlat")

    def get_e_vis_fit_params(self, ana):
        return ana.doc.get("AuxValues").get("EvisFitParams")

    def get_e_vis(self, ana):
        return ana.doc.get("AuxValues").get("Evis")

    def get_e_vis_model(self, ana):
        return ana.doc.get("AuxValues").get("EvisModel")

    def get_sigma_slope(self, ana):
        return ana.doc.get("AuxValues").get("SigmaSlope")

    def get_sigma_null(self, ana):
        return ana.doc.get("AuxValues").get("SigmaNull")

    def get_p_cal(self, ana):
        return ana.pick("Pressure", "cal", self.p_unit)

    def get_err(self, ana):
        return ana.pick("Error", "ind", self.e_unit)

    def get_sigma(self, ana):
        return ana.pick("Sigma", "eff", self.s_unit)

    def get_red_sigma(self, ana):
        return ana.pick("Sigma", "red_eff", "1", dest="AuxValues")

    def get_red_err_temp_corr(self, ana):
        return ana.pick("Error", "red_ind_temp_corr", self.e_unit, dest="AuxValues")

    def get_err_model(self, ana):
        return ana.pick("Error", "model", self.e_unit, dest="AuxValues")


    def e_vis_model_line(self, ana, show=True):
        e_vis = self.get_e_vis_model(ana)
        self.plt.axhline(y=e_vis, label="e_vis_model = {}".format(round(e_vis, 5)))
        if show:
            self.show()

    def e_vis_line(self, ana, show=True):
        e_vis = self.get_e_vis(ana)
        self.plt.axhline(y=e_vis, label="e_vis_cert = {}".format(round(e_vis, 5)))
        if show:
            self.show()

    def check_e_vis(self, ana, show=True):
        x = self.get_red_p_cal(ana)
        y = self.get_red_err(ana)
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("e in {}".format(self.e_unit))
        self.xlog_plot(x , y, label="red. measurement", show=False)
        x = self.get_red_p_cal(ana)
        y = self.get_err_model(ana)
        self.xlog_plot(x , y, linestyle="solid", label="model", marker="None", show=show)


    def plot_e_vis_model(self, ana):
        self.check_e_vis(ana, show=False)
        self.e_vis_model_line(ana)

    def plot_e_vis(self, ana):
        self.check_e_vis(ana, show=False)
        self.e_vis_line(ana)

    def plot_err_diff(self, ana, show=True):
        if show:
            self.plt.cla()
        x = self.get_red_p_cal(ana)
        y0 = self.get_red_err_temp_corr(ana)
        y1 = self.get_red_err(ana)
        y = y0 - y1
        self.plt.xlabel("p in {}".format(self.p_unit))
        self.plt.ylabel("$e_{corr} - e$")
        self.add_point_no(x, y)
        self.xlog_plot(x , y, label="error diff.", show=show)

    def check_sigma(self, ana, show=True):
        self.plt.cla()
        x = self.get_p_cal(ana)
        y = self.get_sigma(ana)
        self.add_point_no(x, y)
        self.plot(x, y, show=show, label="measurement")

    def plot_sigma(self, ana):
        self.plt.cla()
        self.check_sigma(ana, show=False)
        x = self.get_red_p_cal(ana)
        y = self.get_red_sigma(ana)
        self.plot(x, y, show=False, label="red. measurement")
        m = self.get_sigma_slope(ana)
        c = self.get_sigma_null(ana)
        y = m*x+c
        u = self.get_red_u_tot(ana)
        self.plt.errorbar(x, y, yerr=u, label="$m p_{cal} + \sigma_{eff}$ with u(k=1)")
        self.show()
