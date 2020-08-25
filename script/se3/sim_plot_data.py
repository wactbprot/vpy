import sys
import json

import os
sys.path.append(".")
from vpy.analysis import Analysis
from vpy.pkg_io import Io

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure


def main(io, config):
    struct_path = config.get("struct_path")
    cal_file = config.get("cal_file")
    result_name = config.get("result_name")

    doc = io.read_json("{}/{}".format(struct_path, cal_file))

    col_map = ['C0', 'C1','C2', 'C3','C4', 'C5','C6', 'C7','C8','C9']
    font = {'family' : 'normal',
    #'weight' : 'bold',
            'size'   : 18}
    plt.rc('font', **font)
    ana = Analysis(doc, init_dict=doc.get("Calibration").get("Analysis"))

    p_cal = ana.pick("Pressure", "cal", "Pa")

    u_1 = ana.pick("Uncertainty", "p_fill", "1")
    u_2 = ana.pick("Uncertainty", "p_rise", "1")
    u_3 = ana.pick("Uncertainty", "f", "1")
    u_4 = ana.pick("Uncertainty", "V_start", "1")
    u_5 = ana.pick("Uncertainty", "V_add", "1")
    u_6 = ana.pick("Uncertainty", "T_before", "1")
    u_7 = ana.pick("Uncertainty", "T_after", "1")
    u_8 = ana.pick("Uncertainty", "KF", "1")
    u_std = ana.pick("Uncertainty", "standard", "1")

    u_a = ana.pick("Uncertainty", "offset", "1")
    u_b = ana.pick("Uncertainty", "repeat", "1")
    u_c = ana.pick("Uncertainty", "digit", "1")
    u_dev = ana.pick("Uncertainty", "device", "1")

    u_tot = ana.pick("Uncertainty", "total_rel", "1")

    figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')
    plt.plot(p_cal, u_tot*2, 'H-',lw=4, color=col_map[0], label="total (k=2)")

    plt.plot(p_cal, u_dev, 'H:',lw=3, color=col_map[1], label="device (k=1)" )
    plt.plot(p_cal, u_a, '*:',lw=2, color=col_map[9], label="off." )
    plt.plot(p_cal, u_b, 's:',lw=2, color=col_map[3], label="rep." )
    plt.plot(p_cal, u_c, 'D:',lw=2, color=col_map[8], label="dig." )

    plt.plot(p_cal, u_std, 'H-',lw=3, color=col_map[1], label="standard (k=1)" )
    plt.plot(p_cal, u_1, '*-',lw=2, color=col_map[2], label="$p_{fill}$" )
    plt.plot(p_cal, u_2, '*-',lw=2, color=col_map[3], label="$p_{rise}$" )
    plt.plot(p_cal, u_3, 's-',lw=2, color=col_map[4], label="$f_i$" )
    plt.plot(p_cal, u_4, 'D-',lw=2, color=col_map[5], label="$V_{start}$" )
    plt.plot(p_cal, u_5, 'D-',lw=2, color=col_map[6], label="$V_{add}$" )
    plt.plot(p_cal, u_6, 'd-',lw=2, color=col_map[7], label="$T_{before}$" )
    plt.plot(p_cal, u_7, 'd-',lw=2, color=col_map[8], label="$T_{after}$" )
    plt.plot(p_cal, u_8, 'x-',lw=2, color=col_map[9], label="$K_iF_j$" )





    plt.xscale('symlog', linthreshx=1e-12)
    plt.yscale('symlog', linthreshy=1e-12)
    plt.ylim((1e-6, 1e-2))
    plt.xlabel('$p_{}$ in {}'.format("{cal}", "Pa"))
    plt.ylabel('$u$ (relative)')
    plt.grid(True)
    plt.legend()
    plt.savefig("{}.pdf".format(result_name))
    plt.show()


if __name__ == "__main__":
    with open('./script/se3/sim_config.json') as f:
        config = json.load(f)
    io = Io()
    main(io, config)
