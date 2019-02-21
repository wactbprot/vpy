"""
python script/se3/se3_shape_todo.py --min_pressure 90 --max_pressure 130000 --pressure_unit Pa --ids 'cal-2019-se3-ik-4556_0001;cal-2019-se3-ik-4625_0001' --db 'vl_db_work'
"""
import copy
import sys
import json
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
            ids = args[idx_ids].split(';')
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
            todo_pressure_dict = todo.shape_pressure(min=min_pressure, max=max_pressure, unit = todo.pressure_unit)
           
            doc["Calibration"]["ToDo"]["Values"]["Pressure"] = todo_pressure_dict
           
            io.save_doc(copy.deepcopy(doc))
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))        

if __name__ == "__main__":
    main()
       