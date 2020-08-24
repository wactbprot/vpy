import sys
import os
import numpy as np
sys.path.append(os.environ["VIRTUAL_ENV"])
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal
from vpy.pkg_io import Io

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

def main():
    col_map = ['C0', 'C1','C2', 'C3','C4', 'C5','C6', 'C7','C8','C9']
    font = {'family' : 'normal',
    #'weight' : 'bold',
            'size'   : 18}

    plt.rc('font', **font)
    io = Io()
    doc = io.get_doc_db("se3-sim")
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

    figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')
    plt.plot(p_cal, u  , 'H-',lw=3, color=col_map[1], label="total (k=1)" )
    plt.plot(p_cal, u_1, '*-',lw=3, color=col_map[2], label="$p_{fill}$" )
    plt.plot(p_cal, u_2, '*-',lw=3, color=col_map[3], label="$p_{rise}$" )
    plt.plot(p_cal, u_3, 's-',lw=3, color=col_map[4], label="$f_i$" )
    plt.plot(p_cal, u_4, 'D-',lw=3, color=col_map[5], label="$V_{start}$" )
    plt.plot(p_cal, u_5, 'D-',lw=3, color=col_map[6], label="$V_{add}$" )
    plt.plot(p_cal, u_6, 'd-',lw=3, color=col_map[7], label="$T_{before}$" )
    plt.plot(p_cal, u_7, 'd-',lw=3, color=col_map[8], label="$T_{after}$" )
    plt.plot(p_cal, u_8, 'x-',lw=3, color=col_map[9], label="$K$" )

    plt.xscale('symlog', linthreshx=1e-12)
    plt.xlabel('$p_{}$ in {}'.format("{cal}", "Pa"))
    plt.ylabel('$u(p_{cal})$ (relative, k=1)')
    plt.grid(True)
    plt.legend()
    plt.savefig("se3_uncert_overview.pdf")
    plt.show()


if __name__ == "__main__":
    main()
