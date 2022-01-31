import sys
import json

import os
sys.path.append(".")
from vpy.analysis import Analysis
from vpy.pkg_io import Io
from vpy.helper import init_customer_device

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure


def main(io, config):
    struct_path = config.get("struct_path")
    cal_file = config.get("cal_file")
    result_name = config.get("result_name")
    plot_title = config.get("plot_title")
    font = config.get("plot_font")
    col_map =  config.get("plot_col_map")

    p_se2 = (0.01,
             0.02,
             0.05,
             0.1,
             0.2,
             0.5,
            1,
            2,
            5,
             10,
             20,
            30,
            50,
            100)
    u_se2_k1 = (1.38E-03,
                1.07E-03,
                9.64E-04,
                9.46E-04,
                9.39E-04,
                9.23E-04,
                8.61E-04,
                8.47E-04,
                8.43E-04,
                7.70E-04,
                7.65E-04,
                7.50E-04,
                7.48E-04,
                7.47E-04)

    plt.rc('font', **font)
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
    u_std = ana.pick("Uncertainty", "standard", "1")

    figure(num=None, figsize=(16, 9), dpi=80, facecolor='w', edgecolor='k')

    plt.plot(p_cal, u_std, '-',lw=3, color=col_map[1], label="SE3 (k=1)" )
    plt.plot(p_se2, u_se2_k1, ':',lw=3, color=col_map[10], label="SE2 (k=1)" )
    plt.plot(p_cal, u_1,   '-',lw=2, color=col_map[2], label="$p_{fill}$" )
    plt.plot(p_cal, u_2,   '-',lw=2, color=col_map[3], label="$p_{rise}$" )
    plt.plot(p_cal, u_3,   '-',lw=2, color=col_map[4], label="$f_i$" )
    plt.plot(p_cal, u_4,   '-',lw=2, color=col_map[5], label="$V_{start}$" )
    plt.plot(p_cal, u_5,   '-',lw=2, color=col_map[6], label="$V_{add}$" )
    plt.plot(p_cal, u_6,   '-',lw=2, color=col_map[7], label="$T_{before}$" )
    plt.plot(p_cal, u_7,   '-',lw=2, color=col_map[8], label="$T_{after}$" )
    plt.plot(p_cal, u_8,   '-',lw=2, color=col_map[9], label="$K_iF_j$" )

    #plt.title("Uncertainty contributions SE3")

    plt.xscale('symlog', linthreshx=1e-12)
    #plt.yscale('symlog', linthreshy=1e-12)
    #plt.ylim((1e-7, 1.2e-3))
    plt.xlabel('$p_{cal}$ in Pa')
    plt.ylabel('$u(p)/p$')
    plt.grid(True)
    plt.legend()
    plt.savefig("{}.pdf".format(result_name),transparent=True, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    with open('./script/se3/sim_config.json') as f:
        config = json.load(f)
    io = Io()
    main(io, config)
