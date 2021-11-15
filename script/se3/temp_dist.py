"""
python script/se3/temp_dist.py --ids cal-2020-se3-kk-75127_0001 --srv http://a73434:5984 --point 2
python script/se3/temp_dist.py -n # gets the temp. dist -n(ow)
"""
import sys
sys.path.append(".")

import datetime
import requests
import json

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import numpy as np

from vpy.pkg_io import Io
from vpy.standard.se3.cal import Cal
from vpy.values import Temperature
from vpy.device.dmm import Dmm


with open('./script/se3/temp_dist_config.json') as f:
    conf = json.load(f)

conf_dev_hub = conf.get("dev_hub")
conf_plot = conf.get("plot")

date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
channels = list(range(1001, 1031)) + list(range(2001, 2029))

y_t = 980 # mm t ... total
dy_o = 110 # o ... outer
r_i = 180 # i ... inner
n_h = 200 # h ... helper circles

r_o = 280
n_i = 7
n_o = 12

o_v = 2*np.pi/n_i ## offset stirn vorn
o_o = 2*np.pi/n_o ## offset mantel
o_h = 2*np.pi/n_i ## offset stirn hinten

dir_vec =  ["cw",   "cw",   "ccw",    "ccw",    "ccw",  "ccw",  "ccw",   "ccw",   "ccw",   "cw",   "cw",]
dist_vec = ["a",    "a",    "e",      "o",      "e",    "o",    "e",     "o",     "e",     "a",    "a",  ]
o_vec =    [0,      o_v,    o_o,      3*o_o,    3*o_o,  5*o_o,  5*o_o,   7*o_o,   7*o_o,   0,      o_h,  ]
n_vec =    [1,      n_i,    n_o,      n_o,      n_o,    n_o,    n_o,     n_o,     n_o,     1,      n_i,  ]
y_vec =    [-y_t/2, -y_t/2, -dy_o*3,  -dy_o*2,  -dy_o,  0,      dy_o,    dy_o*2,  dy_o*3,  y_t/2,  y_t/2,]
r_vec =    [0,      r_i,    r_o,      r_o,      r_o,    r_o,    r_o,     r_o,     r_o,     0,      r_i,  ]
rh_vec =   [r_o,    r_i,    r_o,      r_o,      r_o,    r_o,    r_o,     r_o,     r_o,     r_o,    r_i,  ]

def gen_x(alpha, r):
    return r * np.sin(alpha)

def gen_z(alpha, r):
    return r * np.cos(alpha)

def gen_alpha(n, o, d="cw"):
    s = -2*np.pi/n
    e =  2*np.pi * (1-1/n)-2*np.pi/n
    if d == "cw":
        return np.linspace(s, e, n) + o
    else:
        return np.linspace(e, s, n) + o

def put_sensor(d, i):
    if d == "a":
        return True
    if d == "e":
        if i % 2:
            return False
        else:
            return True
    if d == "o":
        if i % 2:
            return True
        else:
            return False

def main():
    io = Io()
    io.eval_args()

    if io.ids:
        doc = io.get_doc_db(io.ids[0])
        cal = Cal(doc)

        t_arr = cal.Temp.get_array("ch_", channels, "_after", "C")
        cor_arr = cal.TDev.get_array("corr_ch_", channels,"", "K")

        if io.args.point:
            p = int(io.args.point[0])
        else:
            p = -1

    if io.n:
        doc = io.get_base_doc("se3")

        res = requests.post(conf_dev_hub.get("url"), json=conf_dev_hub.get("dmm_task"))
        res = res.json()
        doc["Measurement"] = {"Values":{"Temperature":res.get("Result")}}
        cal = Cal(doc)

        t_arr = cal.Temp.get_array("ch_", channels, "_now", "C")
        cor_arr = cal.TDev.get_array("corr_ch_", channels,"", "K")

        p = 0

    t = t_arr + cor_arr
    t_i = np.array([e[p] for e in t])

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    x_arr = []
    y_arr = []
    z_arr = []
    sl_arr = [] ## sensor labels
    cl_arr = [] ## chamber labels

    s = 0
    for i, _ in enumerate(y_vec):
        alpha = gen_alpha( n_vec[i], o_vec[i], dir_vec[i])
        x = gen_x(alpha, r_vec[i])
        y = np.full(n_vec[i], y_vec[i])
        z = gen_z(alpha, r_vec[i])

        for j in range(0, n_vec[i]):
            if put_sensor(dist_vec[i], j):
                x_arr.append(x[j])
                y_arr.append(y[j])
                z_arr.append(z[j])
                cl = "$C_{}{}{} D_{}{}{}$".format("{",i,"}","{",j,"}")
                cl_arr.append(cl)
                sl = "$ch_{}{}{}$".format("{",channels[s], "}")
                sl_arr.append(sl)
                ax.text(x[j], y[j], z[j], sl)
                ## next sensor:
                s=s+1

        ## helper
        if i != 0 and i != 9:
            alpha = gen_alpha(n_h, 0)
            x = gen_x(alpha, rh_vec[i])
            y = np.full(n_h, y_vec[i])
            z = gen_z(alpha, rh_vec[i])
            ax.plot(x, y, z, c= "lightgray")

    fig.colorbar(
        ax.scatter(x_arr, y_arr, z_arr,
                   c = t_i,
                   cmap = conf_plot.get("color_map"),
                   s = conf_plot.get("sphere_size"),
                   alpha = 0.5),
        ax=ax)

    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('w')
    ax.yaxis.pane.set_edgecolor('w')
    ax.zaxis.pane.set_edgecolor('w')

    ax.grid(False)

    ax.set_title(conf_plot.get("title").format(date=date))
    ax.set_xlabel(conf_plot.get("xlab"))
    ax.set_zlabel(conf_plot.get("zlab"))
    ax.set_ylabel(conf_plot.get("ylab"))

    f = conf_plot.get("axis_enlarge")

    ax.set_xlim3d(-f*r_o, f*r_o)
    ax.set_ylim3d(-y_t, y_t)
    ax.set_zlim3d(-f*r_o, f*r_o)

    plt.show()

if __name__ == "__main__":
    main()
