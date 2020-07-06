"""
python script/se3/temp_dist.py --ids cal-2020-se3-kk-75127_0001 --srv http://a73434:5984
"""


from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
from vpy.pkg_io import Io
from vpy.standard.se3.cal import Cal

from matplotlib.colors import LinearSegmentedColormap

y_t = 980 # mm t ... total
dy_o = 110 # o ... outer
r_i = 180 # i ... inner
r_o = 280

n_i = 7
n_o = 12
n_h = 200 # helper circles

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
def takeClosest(num,collection):
   return min(collection,key=lambda x:abs(x-num))

def main():
    io = Io()
    io.eval_args()
    for id in io.ids:
        doc = io.get_doc_db(id)

    cal = Cal(doc)
    channels = list(range(1001, 1031)) + list(range(2001, 2029))
    t_arr = cal.Temp.get_array("ch_", channels, "_after", "C")
    cor_arr = cal.TDev.get_array("corr_ch_", channels,"", "K")

    t = t_arr + cor_arr
    i = 0
    t_i = np.array([e[i] for e in t])
    t_min = np.min(t_i)
    t_max = np.max(t_i)

    dl = np.linspace(0,1,len(channels))
    color_list = plt.cm.coolwarm(dl)


    o_o = np.pi/n_o
    o_h = 4*np.pi/n_i
    dir_vec =  ["cw",   "cw",   "cw",     "cw",     "cw",   "cw",  "cw",   "cw",   "cw",   "cw",   "ccw", ]
    dist_vec = ["a",    "a",    "e",      "o",      "e",    "o",   "e",    "o",    "e",    "a",    "a",   ]
    o_vec =    [0,      0,      o_o,      o_o,      o_o,    o_o,   o_o,    o_o,    o_o,    0,      o_h,   ]
    n_vec =    [1,      n_i,    n_o,      n_o,      n_o,    n_o,   n_o,    n_o,    n_o,    1,      n_i,   ]
    y_vec =    [-y_t/2, -y_t/2, -dy_o*3,  -dy_o*2,  -dy_o,  0,     dy_o,   dy_o*2, dy_o*3, y_t/2,  y_t/2, ]
    r_vec =    [0,      r_i,    r_o,      r_o,      r_o,    r_o,   r_o,    r_o,    r_o,    0,      r_i,   ]


    fig = plt.figure(figsize=plt.figaspect(0.5)*1.5)
    ax = fig.gca(projection='3d')

    s = 0
    for i, _ in enumerate(y_vec):

        alpha = gen_alpha( n_vec[i], o_vec[i], dir_vec[i])
        x = gen_x(alpha, r_vec[i])
        y = np.full(n_vec[i], y_vec[i])
        z = gen_z(alpha, r_vec[i])



        for j in range(0, n_vec[i]):
            if put_sensor(dist_vec[i], j):
                s_label = "ch_{}".format(channels[s])
                t = t_i[s]
                r = (t-t_min)/(t_max - t_min)
                cl = takeClosest(r, dl)
                k = np.where(cl == dl)[0][0]

                s=s+1
                c_label="$D_{}{}{}$".format("{",j,"}")
                ax.scatter(x[j],   y[j], z[j], s=np.pi*0.5**2*100, c=color_list[k], alpha=0.75)

            #ax.text(x[j], y[j], z[j], c_label)
            ax.text(x[j], y[j], z[j], s_label )

        ## helper
        alpha = gen_alpha(n_h, 0)
        x = gen_x(alpha, r_vec[i])
        y = np.full(n_h, y_vec[i])
        z = gen_z(alpha, r_vec[i])
        #ax.plot(x, y, z, label="$C_{}{}{}$".format("{",i,"}"))
        ax.plot(x, y, z, c= "lightgray")
    ax.set_xlabel('window $\\rightarrow$ dkm')
    ax.set_zlabel('bottom $\\rightarrow$ top')
    ax.set_ylabel('wall $\\rightarrow$ se1')
    ax.set_xlim3d(-r_o, r_o)
    ax.set_ylim3d(-0.5*y_t, 0.5*y_t)
    ax.set_zlim3d(-r_o, r_o)
    plt.legend(ncol=2)
    plt.show()

if __name__ == "__main__":
    main()
