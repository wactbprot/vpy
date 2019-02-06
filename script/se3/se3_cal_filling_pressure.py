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

        # loop over all filling pressure CDGs and get the total uncertainty
        for i in range(N):
            Dev = cal.FillDevs[i]

            u_i = Dev.get_total_uncert(fill_target, target_unit, target_unit)
            u.append(u_i)
        
        # calculate rel. uncert
        u_rel = u/fill_target + u_f_rel

        # calculate rel. combined uncert. of all devices by 1/u = sqrt( sum (1/u_rel^2))
        u_1 = np.nansum(np.power(u_rel, -2), axis=0)
        u_2 = np.sqrt(u_1)
        out = (u_2 == 0.0)
        if len(out) > 0:
            u_2[out] = np.nan
        u_rel = np.power(u_2, -1)

        out = (u_rel == 0.0)
        if len(out) > 0:
            u_rel[out] = np.nan
           
        out = ( fill_target < 4.0)  
        if len(out) > 0:
           u_rel[out] = np.nan
        
        out = ( fill_target > 133000.0)  
        if len(out) > 0:
           u_rel[out] = np.nan

        if not all(np.isnan(u_rel)):
            i = np.nanargmin(u_rel)
            res = {
                "Pressure_fill.Value": fill_target[i], 
                "Pressure_fill.Type":  "target_fill", 
                "Pressure_fill.Unit":  target_unit, 
                "Expansion.Type" : 'name',
                "Expansion.Value": f_name[i] }
        else:
            res = {"error": "all expasion sequences deliver nan"}
        # print writes back to relay server by writing to std.out
        print(json.dumps(res))        

if __name__ == "__main__":
    main()
