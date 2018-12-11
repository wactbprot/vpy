import sys
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd
import tempfile
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.result import Result
from vpy.display import Display
from vpy.standard.se2.cal import Cal
from vpy.standard.se2.uncert import Uncert
from vpy.values import Values
from vpy.todo import ToDo

"""
Bsp. Aufruf:
python se2_calibration_mb.py --id "cal-2018-se2-pn-0118_0001" --db "vl_db_corr" --srv "http://i75422:5984"
python se2_calibration_mb.py --id "cal-2018-se2-kk-75024_0001" --db "vl_db" --srv "http://a73434:5984"
"""

def main():
    io = Io()
    # holt Messdaten aus --db
    io.eval_args()
    meas_doc = io.load_doc()
    # holt Konstanten ect. aus --db
    base_doc = io.get_base_doc("se2")
    # merge der beiden Dokumente
    doc = io.update_cal_doc(meas_doc, base_doc)
    ana = Analysis(doc)
    res = Result(doc)
    val = Values(doc)

    # Berechnungen-Klasse leitet vom Standard se2 ab
    cal = Cal(doc)
    # Unsicherheits-Klasse leitet auch vom Standard se2 ab
    unc = Uncert(doc)

    cal.temperature_after(ana)
    cal.temperature_room(ana)
    cal.pressure_cal(ana)
    cal.pressure_ind(ana)
    cal.pressure_offset(ana)
    cal.pressure_indication_error(ana)
    cal.measurement_time(ana)
    unc.temperature_vessel(ana)
    cal.reject_outliers_index(ana)    
    cal.make_main_maesurement_index(ana)
    cal.make_pressure_range_index(ana)
    cal.make_offset_stability(ana)
    cal.fit_thermal_transpiration(ana)
    cal.make_AuxValues_section(ana)
    res.make_error_table(ana)
    res.make_formula_section(ana)


    # key = self.Pres.round_to_n(p_cal, 2)
    # p_cal = [np.mean(g.values.tolist()) for _, g in pd.DataFrame(p_cal).groupby(key)]

    #print(pd.Series(ana.pick("Pressure","cal","mbar")))
    #print(pd.DataFrame(ana.pick("Pressure","cal","mbar")).head())
    
    doc = ana.build_doc("Analysis", doc)
    doc = res.build_doc("Result", doc)
    io.save_doc(doc)

    disp = Display(doc)
    disp.SE2_CDG_offset_abs().savefig("offset_stability_abs_" + str(doc["Calibration"]["Certificate"]) + ".pdf")
    disp.SE2_CDG_offset_rel().savefig("offset_stability_rel_" + str(doc["Calibration"]["Certificate"]) + ".pdf")
    disp.SE2_CDG_error_plot().savefig("fit_thermal_transpiration_" + str(doc["Calibration"]["Certificate"]) + ".pdf")

    print("*******")
    p_cal = ana.pick("Pressure","cal","mbar")
    print("*******")
    res.ToDo.make_average_index(p_cal,"mbar")
    print(res.ToDo.average_index)
    print(5<3<5)
    a=np.pi**50
    print(val.round_to_uncertainty(a,0.097,2))
    print(val.round_to_uncertainty_array([123,456,789],[0.01,1,10],2))
    print(val.round_to_uncertainty(0.,0.01,2))
    print(doc["Calibration"]["CustomerObject"]["Class"])
    print(doc["Calibration"]["CustomerObject"]["Owner"]["Name"])
    print(doc["Calibration"]["ToDo"]["Name"])
    print(doc["Calibration"]["ToDo"]["Values"]["Pressure"]["Unit"])
    print(doc["Calibration"]["ToDo"]["Type"])
    print(val.unit_convert(5,"Torr","mbar"))
    print(val.unit_convert(5,"Torr"))
    print(val.unit_convert(np.asarray([1,2,3,4]),"Torr"))
    print(val.unit_convert(np.asarray([1,2,3,4]),"C"))
    print(val.unit_convert(np.asarray([1,2,3,4]),"C","K"))
    print(val.unit_convert(np.asarray([1,2,3,4]),"K","C"))
    print(cal.Cons.get_conv("mbar","Torr"))
    print(val.get_object("Type", "p_fill"))
    print(cal.Cons.get_conv("C", "K"))
    bana = Analysis({})
    print(bana.doc)
    bana.store("myquant", "mytype", [1,2,3], "myunit")
    print(bana.doc)
    print(bana.org)
    print(bana.pick("myquant","mytype","myunit"))
    bana2 = Analysis({'Values': {'myquant': [{'Type': 'mytype', 'Value': [1, 2, 3], 'Unit': 'myunit'}]}})
    print(bana2.org)
    print(bana2.pick("myquant","mytype","myunit"))

if __name__ == "__main__":
    main()
