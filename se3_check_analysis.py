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
    res = {'ok':True}
    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids].split(';')
        except:
           fail = True
        
        
    
    if not fail and len(ids) >0:
        for id in ids:
            doc = io.get_doc_db(id)
           
    else:
        res = {"error": "no --Ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(res))        

if __name__ == "__main__":
    main()
