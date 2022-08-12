import sys
sys.path.append(".")

import json
import numpy as np
import os

from vpy.pkg_io import Io
from vpy.standard.se3.cal import Cal
from vpy.standard.se3.uncert import Uncert

## ---
## python script/se3/cal_filling_pressure_fm_fs.py --target_pressure 0.0001 --pressure_unit "Pa"
## ---

def get_fill_pressures(cal, target_pressure, target_unit):
    if cal.unit == target_unit:

        return target_pressure / cal.get_value("f_s", "1")[0]/ cal.get_value("f_m", "1")[0]
    else:
        sys.exit("units dont match")


def gen_result_dict(target_fill, target_unit):
    return {"Pressure_fill":{"Value": target_fill,
                             "Type": "target_fill",
                             "Unit": target_unit},
            "Expansion":{"Type" : "name",
                         "Value": "f_ms"}}

def main(cal):
    args = sys.argv
    fail = False

    if '--target_pressure' in args:
        idx_p = args.index('--target_pressure') + 1
        try:
             target_pressure = float(args[idx_p])
        except:
           fail = True

    if '--pressure_unit' in args:
        unit_i = args.index('--pressure_unit') + 1
        try:
            target_unit = str(args[unit_i])
        except:
           fail = True

    if not fail:
        target_fill = get_fill_pressures(cal, target_pressure, target_unit)
        res = gen_result_dict(target_fill, target_unit)

        print(json.dumps(res))

if __name__ == "__main__":

    io = Io()
    base_doc = io.get_base_doc(name="se3")
    cal = Cal(base_doc)
    main(cal)
