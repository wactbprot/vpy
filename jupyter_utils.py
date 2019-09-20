
def print_uncert(u):
    d_str = "Type:\t{tp}, Value:\t{val}, Unit:\t{unit}, From\t{f}, To\t{t}, RangeUnit:\t{runit}\nDescr.:\t{descr}\n"
    p_str = d_str.format(tp=u.get("Type"),val=u.get("Value"), unit=u.get("Unit"), f=u.get("From"), t=u.get("To"), runit=u.get("RangeUnit"), descr=u.get("Comment",u.get("Description")))
    print(p_str)
    
def gen_uncert_contrib(tp, val, unit, f, t, runit, descr, source="device", uncert_type="B", dist="norm"):
    r_str = "valid in the range from {f}{runit} to {t}{runit}"
    r_statement = r_str.format(f=f, t=t, runit=runit)
    return {
            "Type":tp,
            "Value":val,
            "Source": source,
            "UncertType": uncert_type,
            "Dist":dist,
            "Unit":unit,
            "From": f,
            "To":t,
            "RangeUnit": runit,
            "Description": "{descr}, ({r_statement})".format(descr=descr, r_statement=r_statement)
           }

def get_idx(l, f, t):
    return [i for i, v in enumerate(l) if v > f and v < t]

def rect_to_norm(u_rect):
    return u_rect/3.0**(0.5)

def store_range(doc, min_p, max_p, unit):
    doc["CalibrationObject"]["Setup"]["UseFrom"] = min_p    
    doc["CalibrationObject"]["Setup"]["UseTo"] = max_p    
    doc["CalibrationObject"]["Setup"]["UseUnit"] = unit
    
    return doc

def store_uncert_list(doc, uncert_list):
    doc["CalibrationObject"]["Uncertainty"] = uncert_list
    
    return doc

def gen_interpol_list(p, e, u, p_unit, e_unit, u_unit):
    return [{
                "Type": "p_ind",
                "Unit": p_unit,
                "Value": list(p)
            },
                {
                "Type": "e",
                "Unit": e_unit,
                "Value": list(e)
            },
                {
                "Type": "u",
                "Unit": u_unit,
                "Value": list(u)
            }]