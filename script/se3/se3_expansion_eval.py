import sys
import os
sys.path.append(os.environ["VIRTUAL_ENV"])

import json
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal as CalSe3
from vpy.standard.se3.uncert import Uncert as UncertSe3

from vpy.standard.frs5.cal import Cal as CalFrs
from vpy.standard.frs5.uncert import Uncert as UncertFrs
 
from vpy.standard.se3.uncert import Uncert
from vpy.device.cdg import Cdg


def main():
    io = Io()
    io.eval_args()
    args = sys.argv
    fail = False
    ret = {'ok':True}
    unit = "Pa"
    
    if '--ids' in args:
        idx_ids = args.index('--ids') + 1 
        try:
            ids = args[idx_ids]
            ids = ids.split('@')
        except:
           fail = True
   
    if not fail and len(ids) >0:
        for id in ids:
            id = id.replace("\"", "")
            expansion = "f_l"
            ## se3
            base_doc_se3 = io.get_base_doc("se3")
            doc = io.get_doc_db(id)
            doc = io.update_cal_doc(doc, base_doc_se3)
               
            res = Analysis(doc, analysis_type="expansion")
            uncert_se3 = UncertSe3(doc)
            cal_se3 = CalSe3(doc)
            
            cal_se3.pressure_gn_corr(res)
            cal_se3.pressure_gn_mean(res) 
            cal_se3.temperature_before(res)
            cal_se3.temperature_after(res)
            cal_se3.temperature_room(res)
            cal_se3.real_gas_correction(res)
            cal_se3.correction_delta_height(res)

            customer_device = doc['Calibration']['CustomerObject']
            CustomerDevice = Cdg(doc, customer_device)
            
            temperature_dict = res.pick_dict('Temperature', 'before')
            gas = cal_se3.get_gas()
            ind_dict = cal_se3.Pres.get_dict('Type', 'nd_ind' )
            offset_dict = cal_se3.Pres.get_dict('Type', 'nd_offset' )
          
            ind = CustomerDevice.pressure(ind_dict, temperature_dict, unit=unit, gas=gas)
            offset = CustomerDevice.pressure(offset_dict, temperature_dict, unit=unit, gas=gas)
          
            print("-------------------sd p_nd:")
            print(ind_dict["SdValue"])
            print(offset_dict["SdValue"])
            p_nd = ind - offset
            print(p_nd)
            
            rg = res.pick("Correction", "rg", "1")
            dh = res.pick("Correction", "delta_heigth", "1")
            p_0, sd_p_0, n_p_0 = res.pick("Pressure", "fill", unit, with_stats=True)
            T_0 = res.pick("Temperature", "before", "K")
            T_1 = res.pick("Temperature", "after", "K")

            print("-------------------u p_o:")
            u_p_0 = uncert_se3.contrib_pressure_fill(p_0, unit, skip_type="A")
            print(u_p_0/p_0)
            u_T_1 = uncert_se3.contrib_temperature_vessel(T_1, "K" , skip_type="A")
            u_T_0 = uncert_se3.contrib_temperature_volume_start(T_0, "K", expansion,  skip_type="A")
            
            ## frs5
            base_doc_frs5 = io.get_base_doc("frs5")
            doc = io.update_cal_doc(doc, base_doc_frs5)

            res = Analysis(doc, analysis_type="expansion")
          
            cal_frs = CalFrs(doc)  
            res = Analysis(doc)
            uncert = UncertFrs(doc)
        
            cal_frs.temperature(res)
            cal_frs.pressure_res(res)
            cal_frs.pressure_cal(res)            
            uncert.total_standard(res)

            p_1 = res.pick("Pressure", "cal", unit)

            corr_tem = T_0 / T_1
            f = (p_1- p_nd ) / (p_0 * rg * dh) * corr_tem
            
            res.store("Pressure", "nd_offset", offset, unit)
            res.store("Pressure", "nd_corr", p_nd, unit)
            res.store("Pressure", "fill", p_0, unit)
            res.store("Pressure", "cal", p_1, unit)
            res.store("Temperature", "before", T_0, "K")
            res.store("Temperature", "after", T_1, "K")
            res.store("Expansion", expansion, f, "1")
            res.store("Correction", "delta_heigth", dh,  "1")
            res.store("Correction", "rg", rg,  "1")
            res.store("Correction", "temperature", corr_tem,  "1")
            
            io.save_doc(res.build_doc())
            #f = np.delete(f, f.argmin())
            #f = np.delete(f, f.argmax())
            print("-------------------f:")
            print(f)
            print(np.mean(f))
            print(np.std(f))
            print(np.std(f)/np.mean(f))
            print(np.std(f)/np.mean(f)/(len(f)-1)**0.5)
            print("-------------------sd p_0:")
            print(sd_p_0/p_0)

if __name__ == "__main__":
    main()
   
