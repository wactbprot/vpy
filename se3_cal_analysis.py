mport sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
from vpy.standard.se3.uncert import Uncert

def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    res = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split(';')
        except:
           fail = True
        
        
    base_doc = io.get_base_doc("se3")
    state_doc = io.get_state_doc("se3") 
    
    if not fail and len(ids) >0:
        for id in ids:
            
            meas_doc = io.get_doc_db(id)
            doc = io.update_cal_doc(meas_doc, base_doc)
            res = Analysis(doc)
 
            cal = Cal(doc)
            cal.insert_state_results(res, state_doc)

            cal.pressure_fill(res)
            cal.temperature_before(res)
            cal.temperature_after(res)
            cal.real_gas_correction(res)
            cal.volume_add(res)
            cal.volume_start(res)
            cal.expansion(res)

            cal.pressure_cal(res)
            cal.pressure_ind(res)
            cal.error(res)

            io.save_doc(res.build_doc())
           
    else:
        res = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(res))        

if __name__ == "__main__":
    main()
