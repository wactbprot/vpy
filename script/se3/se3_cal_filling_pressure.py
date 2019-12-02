import json
import numpy as np
import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

from vpy.pkg_io import Io
from vpy.standard.se3.cal import Cal


def get_expansion_uncert_rel(cal, target_pressure, target_unit):
    if cal.unit == target_unit:
        u_s_rel = cal.get_value("u_f_s", "1")[0]
        u_m_rel = cal.get_value("u_f_m", "1")[0]
        u_l_rel = cal.get_value("u_f_l", "1")[0]

        return np.array([u_s_rel, u_m_rel, u_l_rel])
    else:
        sys.exit("units dont match")

def get_fill_pressures(cal, target_pressure, target_unit):
    if cal.unit == target_unit:
        p_s = target_pressure / cal.get_value("f_s", "1")[0]
        p_m = target_pressure / cal.get_value("f_m", "1")[0]
        p_l = target_pressure / cal.get_value("f_l", "1")[0]
    
        return np.array([p_s, p_m, p_l])
    else:
        sys.exit("units dont match")

def get_fill_pressure_uncert_rel(cal, target_fill, target_unit):
    if cal.unit == target_unit:
        N = len(cal.fill_dev_names)
        u = []
        # loop over all filling pressure CDGs and get the total uncertainty
        for i in range(N):
            Dev = cal.FillDevs[i]
            u_i = Dev.get_total_uncert(target_fill, target_unit, target_unit)
            u.append(u_i)
        
        return cal.Pres.invers_array_sum(u/target_fill)
    else:
        sys.exit("units dont match")

def skip_by_pressure(cal, p, u, unit, min_p=80, max_p=133322, replacement = np.inf):
    if cal.unit == unit:

        out = (p <= min_p)  
        if len(out) > 0:
           u[out] = replacement

        out = (p > max_p)  
        if len(out) > 0:
           u[out] = replacement

        return u
    else:
        sys.exit("units dont match")

def get_min_idx(x):
    if not all(np.isinf(x)):
        return np.nanargmin(x)
    else:
        return np.nan

def gen_result_dict(target_fill, u_rel, target_unit):
        i = get_min_idx(u_rel)
        if np.isnan(i):
            return {"error": "all expasion sequences deliver nan"}
        else:
            return {"Pressure_fill.Value": target_fill[i], 
                    "Pressure_fill.Type":  "target_fill", 
                    "Pressure_fill.Unit":  target_unit, 
                    "Uncertainty_cal.Value": u_rel[i],
                    "Uncertainty_cal.Type": "cal_estimated",
                    "Uncertainty_cal.Unit": "1",
                    "Expansion.Type" : 'name',
                    "Expansion.Value": ["f_s", "f_m", "f_l"][i]}
def main(cal):
    args = sys.argv
    fail = False
    if '--target_pressure' in args:
        idx_p = args.index('--target_pressure') + 1 
        try:
             target_pressure = float(args[idx_p])
        except:
           fail = True
    if '--pressure_unit' in args:
        unit_i = args.index('--pressure_unit') + 1 
        try:
            target_unit = str(args[unit_i])
        except:
           fail = True
    if not fail:
        ## cal target fill p_fill_i from target cal 
        target_fill = get_fill_pressures(cal, target_pressure, target_unit)
        ## cal expasion uncertainties u(f_i)
        f_uncert_rel = get_expansion_uncert_rel(cal, target_pressure, target_unit)
        ## cal filling pressures uncertainties u(p_fill_i)
        fill_uncert_rel = get_fill_pressure_uncert_rel(cal, target_fill, target_unit)
        ## cal total uncert from u(f) and u(p_fill_i)
        ## 
        ## choose filling pressure without f uncert 
        ## until they are determined again
        ## u_rel = np.sqrt(np.power(fill_uncert_rel,2) + np.power(f_uncert_rel, 2))
        u_rel = fill_uncert_rel
        ## skip low and high filling pressures
        u_rel = skip_by_pressure(cal, target_fill, u_rel, target_unit, min_p=50, max_p=133322.0)

        print(json.dumps(gen_result_dict(target_fill, u_rel, target_unit)))

if __name__ == "__main__":

    io = Io()
    base_doc = io.get_base_doc(name="se3") 
    cal = Cal(base_doc)
    main(cal)
