import sys
import os
import pandas as pd
sys.path.append(".")
from vpy.analysis import Analysis
from vpy.pkg_io import Io

def to_si(x):
    return ["\SI{}{:0.1e}{}{}".format("{",y,"}", "{}") for y in x]

def main():
    io = Io()
    doc = io.get_doc_db("cal-sim-se3")
    ana = Analysis(doc, init_dict=doc.get("Calibration").get("Analysis"))


    p_cal = ana.pick("Pressure", "cal", "Pa")
    u_1 = ana.pick("Uncertainty", "p_fill", "1")
    u_2 = ana.pick("Uncertainty", "p_rise", "1")
    u_3 = ana.pick("Uncertainty", "f", "1")
    u_4 = ana.pick("Uncertainty", "V_start", "1")
    u_5 = ana.pick("Uncertainty", "V_add", "1")
    u_6 = ana.pick("Uncertainty", "T_before", "1")
    u_7 = ana.pick("Uncertainty", "T_after", "1")
    u_8 = ana.pick("Uncertainty", "K", "1")
    u = ana.pick("Uncertainty", "standard", "1")

    df = pd.DataFrame({"$p_\text{cal}$/Pa"         : to_si(p_cal),
                       "$u(p_\text{fill})$"        : to_si(u_1),
                       "$u(p_\text{rise})$"        : to_si(u_2),
                       "$u(f)$"                    : to_si(u_3),
                       "$u(V_\text{start})$"       : to_si(u_4),
                       "$u(V_\text{add})$"         : to_si(u_5),
                       "$u(T_\text{before})$"      : to_si(u_6),
                       "$u(T_\text{after})$"       : to_si(u_7),
                       "$u(K)$"                    : to_si(u_8),
                       #"$u_g$"                     : to_si(u),
                       "$U_g$"                     : to_si(u*2),
                       "$U_g\cdot p_\text{cal}$/Pa" :to_si(u*2*p_cal),
                       })

    print(df.to_latex(index=False, escape=False))

    with open('se3-uncert-contrib.tex', 'w') as tf:
        tf.write(df.to_latex(index=False, escape=False))

if __name__ == "__main__":
    main()
