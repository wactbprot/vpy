from ..display.display import Display

class SE3(Display):
    
    non_linestyle = "None"
    norm_markersize = 10
    norm_marker = "o"
    
    def __init__(self, doc):
        super().__init__(doc)
        
    def plot(self, x, y, label="data", show=True):        
        self.plt.plot(x, y,
                      marker = self.norm_marker,
                      linestyle = self.non_linestyle,
                      markersize = self.norm_markersize,
                      label=label)
        if show:
            self.plt.title(self.main_title)
            self.plt.legend()
            self.plt.grid()
            self.plt.show()
        
    def xlog_plot(self, x, y, label="data", show=True):    
        self.plt.xscale('symlog', linthreshx=1e-12)
        self.plot(x, y, label=label, show=show)    
    
    def check_p_e(self, x, y, label="measurement", p_unit="Pa", e_unit="1", show=True):
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(p_unit))
        self.plt.ylabel("e in {}".format(e_unit))
        self.xlog_plot(x , y, label=label, show=show)
        
    def check_p_sigma(self, x, y, label="measurement", p_unit="Pa", e_unit="1", show=True):
        self.add_point_no(x, y)
        self.plt.xlabel("p in {}".format(p_unit))
        self.plt.ylabel("$\sigma_{eff}$ ")
        self.plot(x , y, label=label, show=show)

    def e_vis_line(self, e_vis, show=True):
        self.plt.axhline(y=e_vis, label="e_vis = {}".format(round(e_vis, 5)))

    def plot_p_ediff(self, x, y, p_unit="Pa", e_unit="1", show=True):
        if show:
            self.plt.cla()
        self.plt.xlabel("p in {}".format(p_unit))
        self.plt.ylabel("$e_{corr} - e$")
        self.add_point_no(x, y)
        self.xlog_plot(x , y, label="error diff.", show=show)       

    def plot_p_e_u(self, x, y, u, show=True):
        if show:
            self.plt.cla()
        self.plt.errorbar(x, y,   yerr=u, label="certificate")

