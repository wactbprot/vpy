import sys
sys.path.append(".")

from vpy.pkg_io import Io
import numpy as np
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
import sys
import json

def main():
    io = Io()
    args = sys.argv
    fail = False

    if '--target_pressure' in args:
        target_i = args.index('--target_pressure') + 1
        try:
            target_pressure = float(args[target_i])
        except:
           fail = True

    if '--pressure_unit' in args:
        unit_i = args.index('--pressure_unit') + 1
        try:
            pressure_unit = str(args[unit_i])
        except:
           fail = True

    if not fail:
        res = {"Pressure_compare":{"Value": target_pressure,
                                   "Type":  "target_compare",
                                   "Unit":  pressure_unit}}
    else:
        res = {"error": "on attempt to parse params"}

    print(json.dumps(res))

if __name__ == "__main__":
    main()
