import sys
import os
import json
import pandas as pd
sys.path.append(".")
from vpy.analysis import Analysis
from vpy.pkg_io import Io
from vpy.helper import init_customer_device

def to_si(x):
    return ["\SI{}{:0.1e}{}{}".format("{",y,"}", "{}") for y in x]

def main(io, config):
    struct_path = config.get("struct_path")
    cal_file = config.get("cal_file")
    result_name = config.get("result_name")

    doc = io.read_json("{}/{}".format(struct_path, cal_file))

    ana = Analysis(doc, init_dict=doc.get("Calibration").get("Analysis"))
    cuco = init_customer_device(doc)

    p_cal = ana.pick("Pressure", "cal", "Pa")
    u_1 = ana.pick("Uncertainty", "p_fill", "1")
    u_2 = ana.pick("Uncertainty", "p_rise", "1")
    u_3 = ana.pick("Uncertainty", "f", "1")
    u_4 = ana.pick("Uncertainty", "V_start", "1")
    u_5 = ana.pick("Uncertainty", "V_add", "1")
    u_6 = ana.pick("Uncertainty", "T_before", "1")
    u_7 = ana.pick("Uncertainty", "T_after", "1")
    u_8 = ana.pick("Uncertainty", "KF", "1")
    u = ana.pick("Uncertainty", "standard", "1")

    df = pd.DataFrame({"$p_\text{cal}$/Pa"         : to_si(p_cal),
                       "$u(p_\text{fill})$"        : to_si(u_1),
                       "$u(p_\text{rise})$"        : to_si(u_2),
                       "$u(f)$"                    : to_si(u_3),
                       "$u(V_\text{start})$"       : to_si(u_4),
                       "$u(V_\text{add})$"         : to_si(u_5),
                       "$u(T_\text{before})$"      : to_si(u_6),
                       "$u(T_\text{after})$"       : to_si(u_7),
                       "$u(K_iF_i)$"               : to_si(u_8),
                       #"$u_g$"                     : to_si(u),
                       "$U_{\text{SE3}}$"                     : to_si(u*2),
                       "$U_{\text{SE3}}\cdot p_\text{cal}$/Pa" :to_si(u*2*p_cal),
                       })

    print(df.to_latex(index=False, escape=False))

    with open("{}.tex".format(result_name), 'w') as tf:
        tf.write(df.to_latex(index=False, escape=False))

    u_1 = ana.pick("Uncertainty", "offset", "1")
    u_2 = ana.pick("Uncertainty", "repeat", "1")
    u_3 = ana.pick("Uncertainty", "digit", "1")
    u_4 = ana.pick("Uncertainty", "device", "1")
    u_5 = ana.pick("Uncertainty", "total_rel", "1")

    df = pd.DataFrame({"$p_\text{cal}$/Pa"     : to_si(p_cal),
                       "$u_{\text{SE3}}$"      : to_si(u),
                       "$u_{\text{offset}}$"   : to_si(u_1),
                       "$u_{\text{repeat}}$"   : to_si(u_2),
                       "$u_{\text{digit}}$"    : to_si(u_3),
                       "$u_{\text{CDG}}$"      : to_si(u_4),
                       "$u_{\text{ges.}}$"     : to_si(u_5),
                       "$U_{\text{ges.}}$"     : to_si(u_5*2),
                       "$U_{\text{ges.}}\cdot p_\text{cal}$/Pa$"     : to_si(u_5*2*p_cal),
                       })

    with open("{}_{}_{}_{}.tex".format(result_name, cuco.dev_class, cuco.type_head, cuco.producer.upper()), 'w') as tf:
        tf.write(df.to_latex(index=False, escape=False))

if __name__ == "__main__":
    with open('./script/se3/sim_config.json') as f:
        config = json.load(f)

    io = Io()
    main(io, config)
