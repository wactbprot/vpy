"""
python script/se2/se2_cal_analysis.py --ids 'cal-2019-se2-kk-75026_0001'  --srv 'http://a73434:5984' -u -s
"""
import sys
import os
sys.path.append(".")

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se2.cal import Cal

from vpy.standard.se2.std import Se2

from vpy.device.cdg import InfCdg, Cdg
from vpy.device.srg import Srg
from vpy.device.rsg import Rsg


def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}

    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids]
            ids = ids.split('@')
        except:
           fail = True

    if '-u' in args:   # erzeugt Einträge für KOnstatne und Calibrierobjekte
        update = True
    else:
        update = False
    
    if not fail and len(ids) >0:
        base_doc = io.get_base_doc("se2")
        for id in ids:
            id = id.replace("\"", "")

            doc = io.get_doc_db(id)
            if update:
                doc = io.update_cal_doc(doc, base_doc)

            ana = Analysis(doc, analysis_type="expansion")
            cal = Cal(doc)
            
            if 'CustomerObject' in doc['Calibration']:
                customer_device = doc['Calibration']['CustomerObject']
                dev_class = customer_device.get('Class', "generic")
                if dev_class == 'SRG':
                    CustomerDevice = Srg(doc, customer_device)
                if dev_class == 'CDG':
                    CustomerDevice = Cdg(doc, customer_device)
                if dev_class == 'RSG':
                    CustomerDevice = Rsg(doc, {})
      
            cal.temperature_after(ana)
            cal.temperature_room(ana)
            cal.pressure_cal(ana)
            cal.pressure_ind(ana)
            cal.pressure_offset(ana)
            cal.pressure_indication_error(ana)
            cal.measurement_time(ana)
            cal.faktor(ana)

            io.save_doc(ana.build_doc())
           
    else:
        ret = {"error": "no --ids found"}
        # print writes back to relay server by writing to std.out
    
    print(json.dumps(ret))
if __name__ == "__main__":
    main()
