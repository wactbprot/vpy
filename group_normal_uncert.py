import pandas as pd
import numpy as np

from vpy.device.cdg import InfCdg
from vpy.pkg_io import Io

def main():
    io = Io()
    p = np.logspace(-1,3,40)
    u_t = []

    heads = ["1T_1", "1T_2","1T_3",
            "10T_1", "10T_2","10T_3",
            "100T_1", "100T_2","100T_3",
            "1000T_1", "1000T_2","1000T_3",]
    for head in heads:
        const_doc = io.get_doc_db("constants")
        cdg_doc = io.get_doc_db("cob-cdg-se3_{}".format(head))

        cdg = InfCdg(const_doc, cdg_doc)
        u = cdg.get_total_uncert(p, "mbar", "mbar")
        u_t.append(u/p)


    u_c = np.power(np.nansum(np.power(u_t, -1), axis=0), -1)

    p_f = ['{:.1e}'.format(i) for i in p]
    u_f = ['{:.1e}'.format(i) for i in u_c]
    u_f2 = ['{:.1e}'.format(i) for i in u_c*2]
    df = pd.DataFrame({"$p$ in mbar":p_f, "$u(k=1)$ (relative)":u_f, "$U(k=2)$ (relative)":u_f2})

    print(df.to_latex())

if __name__ == "__main__":
    main()
