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

        p = ana.pick("Pressure", "cal", "Pa")
        ex = ana.org["Calibration"]["Measurement"]["Values"]["Expansion"]["Value"]
        u = np.full(len(p), np.nan)
        for i in range(len(p)):
            if ex[i] == "direkt":
                u[i] = np.piecewise(p[i], [p[i] <= 950., 950. < p[i] <= 8000.,  8000. < p[i]]
                                        , [     0.00035,              0.00019,       0.00014])
            else:
                u[i] = np.piecewise(p[i], [p[i] <= 0.027, 0.027 < p[i] <= 0.3, 0.3 < p[i] <= 0.73, 0.73 < p[i] <= 9., p[i] > 9.]
                                        , [       0.0014,               0.001,            0.00092,           0.00086,   0.00075])
        #print(np.transpose([p,ex,u]))                                
        ana.store("Uncertainty", "standard", u , "1")

    def u_PTB_rel_old(self, ana):

        p_list = ana.pick("Pressure", "cal", "Pa")
        u = np.asarray([np.piecewise(p, [p <= 0.027, (p > 0.027 and p <= 0.3), (p > 0.3 and p <= 0.73), (p >0.73 and p <= 9.), (p > 9. and p <= 1000.), (p > 1000. and p <= 8000.),  8000. < p]
                                       ,[0.0014,                        0.001,                 0.00092,              0.00086,                 0.00075,                   0.00019,  0.00014] ).tolist() for p in p_list])
        ana.store("Uncertainty", "standard", u , "1")        

    def make_offset_stability(self, ana):

        # should outliers by rejected? e.g. forgot to switch
        # measurement range for offset but switched for p_ind

        pr_idx = ana.doc["AuxValues"]["PressureRangeIndex"]
        av_idx = ana.doc["AuxValues"]["AverageIndexFlat"]
        reject_offset_idx = ana.doc["AuxValues"]["RejectIndexOffset"]
        faktor = ana.pick_dict("Faktor", "faktor").get("Value")

        ex = ana.org["Calibration"]["Measurement"]["Values"]["Expansion"]["Value"]
        p_off = ana.pick("Pressure", "offset", "Pa")
        p_ind_corr = ana.pick("Pressure", "ind_corr", "Pa")
        p_ind_corr_max = max([p_ind_corr[i] for i in av_idx])

        print(pr_idx)
        if len(pr_idx) > 1:
            p_range_order_idx = np.argsort([np.mean(np.take(faktor, i)) for i in pr_idx])
            pr_idx = np.take(pr_idx, p_range_order_idx).tolist() #make sure to start with the lowest range
        print(pr_idx)

        offset_unc = np.full(len(p_off), np.nan)
        for i in pr_idx:
            ii = [j for j in i if ex[j]!="direkt" and p_ind_corr[j] < 0.5*p_ind_corr_max and (not j in reject_offset_idx)]
            #falls weniger als 4 Werte, nehme Unsicherheit der nächstkleineren Range
            if len(ii) > 3:
                unc_old = np.std([p_off[j] for j in ii])
                unc0 = unc = np.mean(np.abs(np.diff([p_off[j] for j in ii])))
                print("offset vector: " + str([p_off[j] for j in ii]))
                print("offset std: " + str(unc_old))
                print("offset diff: " + str(unc))
                for j in i: offset_unc[j] = unc
            else:
                for j in i: offset_unc[j] = unc0

        ana.store("Uncertainty", "offset", offset_unc / p_ind_corr, "1")
        ana.store("Uncertainty", "offset_abs", offset_unc, "Pa")

