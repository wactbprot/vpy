import numpy as np
from vpy.pkg_io import Io
import matplotlib.pyplot as plt
import pandas as pd

def main():
    io = Io()
    dat = io.get_hist_data("se3")
    res = {}
    val = {}
    for d in dat:
        dev_name = dat[d]["Name"]
        dat_date = dat[d]["Date"]
        for o in dat[d]["Interpol"]:
                if o["Type"] == "e":
                    dev_mean = np.mean(o["Value"][-10:-1])

        if dev_name not in res:
            res[dev_name] = {}
        if dev_name not in val:
            val[dev_name] = []

        res[dev_name][dat_date] = round(dev_mean, 4)
        val[dev_name].append(dev_mean)

    for k,v in val.items():
        res[k]["diff."] =v[-1] - v[-2]


    print( pd.DataFrame.from_dict(res).to_latex())
if __name__ == "__main__":
    main()
