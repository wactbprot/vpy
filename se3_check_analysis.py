from vpy.pkg_io import Io
import numpy as np
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal
import sys
import json

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
        
        
    
    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
            if 'Calibration' in doc and 'Analysis' in doc['Calibration']:
                cal = Cal(doc)
                analysis = doc['Calibration']['Analysis']
                res = Analysis(doc, init_dict=analysis)
                chk = Analysis(doc)

                cal.check_analysis(res, chk)
                print(res.build_doc(()))
                
                #io.save_doc(chk.build_doc("Check"))
            else:
                ret = {"error": "doc {} contains no analysis to check".format(id)}
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))        

if __name__ == "__main__":
    main()
