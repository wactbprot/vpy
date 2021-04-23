"""
python script/group_normal/make_ks_tables.py
"""
import sys
import os
sys.path.append(".")

from vpy.pkg_io import Io
f_info = open("script/group_normal/gn_device_table.tex","w+")
io = Io()
devs = io.get_device_info("se3")

def numify(s):
    return "\\num{"+ s + "}"

f_info.write("\\begin{tabular}{ l l l l l }\n")
for _,d in enumerate(devs):
    f_info.write("\\verb|{n}|&\\verb|{id}|&{fs}&{t}&{sn}\\\\\n".format(id=d["id"],n=d["Name"],sn=d["SN"],t=d["Type"],fs=d["FullScale"]))
f_info.write("\\end{tabular}\n")
f_info.close()

f = open("script/group_normal/gn_result_table.tex".format(d["Name"]),"w+")
for _,d in enumerate(devs):
    cob_doc = io.get_doc_db(d["id"])
    interp_dict = cob_doc.get("CalibrationObject").get("Interpol")
    ind_arr = interp_dict[0].get("Value")
    e_arr = interp_dict[1].get("Value")

    f.write("\\begin{table}\\begin{tabular}{l l }\n\\toprule\n")
    f.write("$p$&$e$\\\\\n Pa & relativ \\\\\\midrule\n")
    for i,_ in enumerate(ind_arr):
        p = "{:.3E}".format(ind_arr[i])
        e = "{:.2E}".format(e_arr[i])
        f.write("{}&{}\\\\\n".format(numify(p), numify(e)))
    f.write("\\bottomrule\n\\end{tabular}\\caption{Ergebnisse "+ d["Name"].replace("_", " ") + "}\\end{table}")

f.close()
