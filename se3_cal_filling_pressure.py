from vpy.pkg_io import Io
import numpy as np
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
import sys
import json

def main():
    io = Io()
    args = sys.argv
    fail = False
    if '-p' in args and '-u' in args:
        idx_p = args.index('-p') + 1 
        idx_u = args.index('-u') + 1
        
        try:
            target_pressure = float(args[idx_p])
        except:
           fail = True
        
        try:
            target_unit = args[idx_u]
        except:
           fail = True
    
    if not fail:
        base_doc = io.get_base_doc(name="se3")
        cal = Cal(base_doc)

        f_name = ["f_s", "f_m", "f_l"]

        p_s = target_pressure / cal.get_value("f_s", "1")[0]
        p_m = target_pressure / cal.get_value("f_m", "1")[0]
        p_l = target_pressure / cal.get_value("f_l", "1")[0]
        u_s_rel = cal.get_value("u_f_s", "1")[0]
        u_m_rel = cal.get_value("u_f_m", "1")[0]
        u_l_rel = cal.get_value("u_f_l", "1")[0]
        
        fill_target = np.array([p_s, p_m, p_l])
        u_f_rel = np.array([u_s_rel, u_m_rel, u_l_rel])
 
        N = len(cal.fill_dev_names)
        u = []

        for i in range(N):
            Dev = cal.FillDevs[i]
            u_i = Dev.get_total_uncert(fill_target, target_unit, target_unit)
            u.append(u_i)

        # calculate rel. uncert
        u_rel = u/fill_target 

        # calculate rel. combined uncert. of all devices by 1/u = sqrt( sum (1/u_rel^2))
        u_comb_rel = np.power(np.sqrt(np.nansum(np.power(u_rel, -2), axis=0)), -1)
        
        i = (u_comb_rel == 0.0)
        if len(i) > 0:
            u_comb_rel[i] = np.nan
        
        i = np.nanargmin(u_comb_rel + u_f_rel)
        
        res = {"Pressure_fill.Value": fill_target[i], "Pressure_fill.Unit":  target_unit, "Expansion_name": f_name[i] }
        print(json.dumps(res))        

if __name__ == "__main__":
    main()
