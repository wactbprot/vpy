from vpy.pkg_io import Io
import matplotlib.pyplot as plt
def main():
    io = Io()
    dat = io.get_hist_data("se3")
    labels = []
    markers =[
            ".",
            ",",
            "+",
            ">",
            "^",
            "1",
            "2",
            "3",
            "4",
            "o",
            "v",
            "<"]
    devices = [
             "1T_1"    ,
             "1T_2"   ,
             "1T_3"   ,
             "10T_1"  ,
             "10T_2"  ,
             "10T_3"  ,
             "100T_1" ,
             "100T_2" ,
             "100T_3" ,
             "1000T_1",
             "1000T_2",
             "1000T_3"
            ]
    col = {}
    j = -1
    plt.figure(num=None, figsize=(14, 10), facecolor='w', edgecolor='k')
    for d in dat:
        dev_name = dat[d]["Name"]
        dev_fullscale = dat[d]["FullScale"]
        dat_date = dat[d]["Date"]

        if dev_name in devices:
            i = devices.index(dev_name)
            for o in dat[d]["Interpol"]:
                if o["Type"] == "p_ind":
                    p = o["Value"]
                if o["Type"] == "e":
                    e = o["Value"]

            idx = "{}_{}".format(dat_date, dev_fullscale)
            if idx not in col:
                j = j+1
                col[idx] = j

            plt.semilogx(p, e, marker = markers[i], color = "C{}".format(col[idx]))
            labels.append( "{} at {}".format(dev_name, dat_date))

    plt.title("SE3 group normal")
    plt.xlabel(r'$p_{ind}$ in mbar')
    plt.ylabel(r'$e$ (relative)')
    plt.legend(labels, ncol=4, borderaxespad=0.)
    plt.grid()
    plt.savefig("group_normal_hist.pdf")
    plt.show()
if __name__ == "__main__":
    main()
