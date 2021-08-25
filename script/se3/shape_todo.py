"""
python script/se3/se3_shape_todo.py --min_pressure 90 --max_pressure 130000 --pressure_unit Pa --ids cal-2019-se3-ik-4556_0001@cal-2019-se3-ik-4625_0001 --db 'vl_db_work'
"""

import sys
import json
import copy
import numpy as np
from vpy.pkg_io import Io
from vpy.todo import ToDo
from vpy.analysis import Analysis
from vpy.constants import Constants

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1
        try:
            ids = args[idx_ids].split('@')
        except:
           fail = True

    if '--min_pressure' in args:
        min_i = args.index('--min_pressure') + 1
        try:
            min_pressure = float(args[min_i])
        except:
           fail = True

    if '--max_pressure' in args:
        max_i = args.index('--max_pressure') + 1
        try:
            max_pressure = float(args[max_i])
        except:
           fail = True

    if '--pressure_unit' in args:
        unit_i = args.index('--pressure_unit') + 1
        try:
            pressure_unit = str(args[unit_i])
        except:
           fail = True

    if not fail and len(ids) > 0:
        base_doc = io.get_base_doc("se3")
        for id in ids:
            doc = io.get_doc_db(id)
            todo = ToDo(doc)
            const = Constants(base_doc)
            conv = const.get_conv(from_unit=pressure_unit, to_unit=todo.pressure_unit)

            max_pressure = max_pressure * conv
            min_pressure = min_pressure * conv

            todo_dict, rest_dict = todo.shape_pressure(min_p=min_pressure, max_p=max_pressure, unit = todo.pressure_unit)

            doc["Calibration"]["ToDo"]["Values"]["Pressure"] = todo_dict

            io.save_doc(doc)

            if rest_dict:
                ## generate a new doc with issue+1 and rest todo
                rest_doc = copy.deepcopy(doc)

                id_arr = rest_doc["_id"].split("_")
                issue = str(int(id_arr[-1]) + 1 + 10000)[1:5]
                id_arr[1] = issue

                rest_doc["_id"] = "_".join(id_arr)
                rest_doc["Calibration"]["Issue"] = issue
                rest_doc["Calibration"]["ToDo"]["Values"]["Pressure"] = rest_dict
                del rest_doc["_rev"]

                io.save_doc(rest_doc)

    else:
        ret = {"error": "no --ids found"}

    print(json.dumps(ret))

if __name__ == "__main__":
    main()
