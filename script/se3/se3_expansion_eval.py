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
            ## -------------------------
            ## se3
            ## -------------------------
            base_doc_se3 = io.get_base_doc("se3")
            doc = io.get_doc_db(id)
            doc = io.update_cal_doc(doc, base_doc_se3)
               
            res = Analysis(doc, analysis_type="expansion")
            uncert_se3 = UncertSe3(doc)
            cal_se3 = CalSe3(doc)
            
            f_names = cal_se3.get_expansion_name()
            f_name = f_names[0] 

            cal_se3.pressure_gn_corr(res)
            cal_se3.pressure_gn_mean(res) 
            cal_se3.temperature_before(res)
            cal_se3.temperature_after(res)
            cal_se3.real_gas_correction(res)
            cal_se3.correction_delta_height(res)

            rg = res.pick("Correction", "rg", "1")
            dh = res.pick("Correction", "delta_heigth", "1")
            p_0 = res.pick("Pressure", "fill", unit)
            T_0 = res.pick("Temperature", "before", "K")
            T_1 = res.pick("Temperature", "after", "K")

            u_p_0 = uncert_se3.contrib_pressure_fill(p_0, unit, skip_type="A")
            u_T_1 = uncert_se3.contrib_temperature_vessel(T_1, "K" , skip_type="A")
            u_T_0 = uncert_se3.contrib_temperature_volume_start(T_0, "K", f_names,  skip_type="A")
            
            ## -------------------------
            ## p_nd
            ## -------------------------
            customer_device = doc['Calibration']['CustomerObject']
            CustomerDevice = Cdg(doc, customer_device)
            
            temperature_dict = res.pick_dict('Temperature', 'before')
            gas = cal_se3.get_gas()
            ind_dict = cal_se3.Pres.get_dict('Type', 'nd_ind' )
            offset_dict = cal_se3.Pres.get_dict('Type', 'nd_offset' )
          
            ind = CustomerDevice.pressure(ind_dict, temperature_dict, unit=unit, gas=gas)
            offset = CustomerDevice.pressure(offset_dict, temperature_dict, unit=unit, gas=gas)
          
            p_nd = ind - offset
            u_p_nd = CustomerDevice.get_total_uncert(p_nd, unit, unit, skip_type="A")
            
            ## -------------------------
            ## frs5
            ## -------------------------
            base_doc_frs5 = io.get_base_doc("frs5")
            doc = io.update_cal_doc(doc, base_doc_frs5)

            res = Analysis(doc, analysis_type="expansion")
          
            cal_frs = CalFrs(doc)  
            res = Analysis(doc)
            uncert = UncertFrs(doc)
        
            cal_frs.temperature(res)
            cal_frs.pressure_res(res)
            cal_frs.pressure_cal(res)            
            uncert.total_standard(res, no_type_a=True)

            p_1 = res.pick("Pressure", "cal", unit)
            u_p_1 = res.pick("Uncertainty", "standard", "1")*p_1
            
            ## -------------------------
            ## f
            ## -------------------------
            corr_tem = T_0 / T_1
            f = (p_1 - p_nd ) / (p_0 * rg * dh) * corr_tem
            
            s_p_1 = 1/p_0*corr_tem
            s_p_0 = - (p_1 - p_nd )/ (p_0**2) * corr_tem
            s_p_nd = 1/p_0*corr_tem
            s_T_0 = (p_1 - p_nd ) / (p_0)/T_1
            s_T_1 = - (p_1 - p_nd ) / (p_0)*T_0/T_1**2
            
            uc_p_1  = (s_p_1 *u_p_1)
            uc_p_0  = (s_p_0 *u_p_0)
            uc_p_nd = (s_p_nd *u_p_nd)
            uc_T_1  = (s_T_1 *u_T_1)
            uc_T_0  = (s_T_0 *u_T_0)


            u = (uc_p_1**2 + uc_p_0**2 + uc_p_nd**2 + uc_T_1**2 + uc_T_0**2)**0.5
            
            res.store("Expansion", f_name, f, "1")
            res.store("Pressure", "nd_offset", offset, unit)
            res.store("Pressure", "nd_corr", p_nd, unit)
            res.store("Uncertainty", "nd_corr", u_p_nd, unit)
            res.store("Pressure", "fill", p_0, unit)
            res.store("Uncertainty", "fill", u_p_0, unit)
            res.store("Pressure", "cal", p_1, unit)
            res.store("Uncertainty", "cal", u_p_1*p_1, unit)
            res.store("Temperature", "before", T_0, "K")
            res.store("Temperature", "after", T_1, "K")
            res.store("Uncertainty", "before", u_T_0, "K")
            res.store("Uncertainty", "after", u_T_1, "K")
            res.store("Uncertainty", "total", u, "1")
            res.store("Correction", "delta_heigth", dh,  "1")
            res.store("Correction", "rg", rg,  "1")
            res.store("Correction", "temperature", corr_tem,  "1")
            
            doc = res.build_doc()
            doc["Calibration"]["Standard"] = [base_doc_se3["Standard"], base_doc_frs5["Standard"]]
            
            io.save_doc(doc)
            print("------------------- p_nd:")
            print(p_nd)

            print(ind_dict["SdValue"])
            print(offset_dict["SdValue"])

            print("-------------------u p_0:")
            print(u_p_0/p_0)

            print("-------------------u p_1:")
            print(u_p_1)

            
            print("-------------------u p_nd:")
            print(u_p_nd)

            #f = np.delete(f, f.argmin())
            #f = np.delete(f, f.argmax())
            print("-------------------f:")
            print(f)
            print(np.mean(f))
            print(np.std(f))
            print(np.std(f)/np.mean(f))
            print(np.std(f)/np.mean(f)/(len(f)-1)**0.5)

            print("-------------------u:")
            print(u/f)
            

if __name__ == "__main__":
    main()
   
