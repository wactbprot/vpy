import numpy as np
import sympy as sym
#from .std import Se2

#class Uncert(Se2):
class Uncert:

    def __init__(self, doc):
        #super().__init__(doc)
        pass
    
    def total(self, ana):
        
        p_cal = ana.pick("Pressure", "cal", "mbar")
        p_ind = ana.pick("Pressure", "ind", "mbar")

        offset_uncert = ana.pick("Uncertainty", "offset", "mbar")
        repeat_uncert = ana.pick("Uncertainty", "repeat", "1")
        standard_uncert = ana.pick("Uncertainty", "standard", "1")
        # digitizing error still missing
        u_ind_abs = np.sqrt((p_cal * repeat_uncert)**2 + offset_uncert**2)

        u_rel = 100.0 * p_ind / p_cal * np.sqrt((u_ind_abs / p_ind)**2 + standard_uncert**2)
        
        ana.store("Uncertainty", "total_rel", u_rel , "%")
        ana.store("Uncertainty", "total_abs", u_rel , "1")

    def u_PTB_rel(self, ana):
        
        p_list = ana.pick("Pressure", "cal", "mbar")
        u = np.asarray([np.piecewise(p, [p <= 0.00027, p <= 0.003, p <= 0.0073, p <= 0.09, p <= 10, p <= 80,  80 < p],
                                        [0.0014, 0.001, 0.00092, 0.00086, 0.00075, 0.00019, 0.00014]).tolist() for p in p_list])

        ana.store("Uncertainty", "standard", u , "1")

    def repeat_rel(self, ana):

        p_list = ana.pick("Pressure", "ind", "mbar")
        u = np.asarray([np.piecewise(p, [p <= 0.1, p <= 9.5, p > 9.5], [0.0008, 0.0003, 0.0001]).tolist() for p in p_list])

        ana.store("Uncertainty", "repeat", u, "1")


    def make_offset_stability(self, ana):

        # should outliers by rejected? e.g. forgot to switch
        # measurement range for offset but switched for p_ind

        pr_idx = ana.pressure_range_index
        av_idx = ana.average_index

        idx = [item for sublist in av_idx for item in sublist]

        p_cal = ana.pick("Pressure", "cal", "mbar")
        p_off = ana.pick("Pressure", "offset", "mbar")

        offset_unc = np.full(len(p_off), np.nan)
        for i in pr_idx:
            unc = np.std([p_off[j] for j in i])
            for j in i:
                offset_unc[j] = unc

        ana.store("Uncertainty", "offset", offset_unc, "mbar")

