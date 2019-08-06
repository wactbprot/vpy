import numpy as np
import sympy as sym
#from .std import Se2

#class Uncert(Se2):
class Uncert:

    def __init__(self, doc):
        #super().__init__(doc)
        pass
    
    def total(self, ana):
        
        p_cal = ana.pick("Pressure", "cal", "Pa")
        p_ind = ana.pick("Pressure", "ind_corr", "Pa")

        offset_uncert = ana.pick("Uncertainty", "offset", "Pa")
        repeat_uncert = ana.pick("Uncertainty", "repeat", "1")
        standard_uncert = ana.pick("Uncertainty", "standard", "1")
        # digitizing error still missing
        u_ind_abs = np.sqrt((p_cal * repeat_uncert)**2 + offset_uncert**2)

        u_rel = p_ind / p_cal * np.sqrt((u_ind_abs / p_ind)**2 + standard_uncert**2)
        
        ana.store("Uncertainty", "total_rel", u_rel , "1")
        ana.store("Uncertainty", "total_abs", u_rel * p_cal , "Pa")

    def u_PTB_rel(self, ana):

        p_list = ana.pick("Pressure", "cal", "Pa")
        u = np.asarray([np.piecewise(p, [p <= 0.027, (p > 0.027 and p <= 0.3), (p > 0.3 and p <= 0.73), (p >0.73 and p <= 9.), (p > 9. and p <= 1000.), (p > 1000. and p <= 8000.),  8000. < p]
                                       ,[0.0014,                        0.001,                 0.00092,              0.00086,                 0.00075,                   0.00019,  0.00014] ).tolist() for p in p_list])
        ana.store("Uncertainty", "standard", u , "1")

    def make_offset_stability(self, ana):

        # should outliers by rejected? e.g. forgot to switch
        # measurement range for offset but switched for p_ind

        pr_idx = ana.doc["AuxValues"]["PressureRangeIndex"]
        av_idx = ana.doc["AuxValues"]["AverageIndex"]

        idx = [item for sublist in av_idx for item in sublist]

        p_off = ana.pick("Pressure", "offset", "Pa")
        p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")

        # offset_unc = np.nanstd(p_off)

        offset_unc = np.full(len(p_off), np.nan)
        for i in pr_idx:
            unc = np.std([p_off[j] for j in i])
            for j in i:
                offset_unc[j] = unc

        ana.store("Uncertainty", "offset", offset_unc / p_ind_corr, "1")
        ana.store("Uncertainty", "offset_abs", offset_unc, "Pa")

