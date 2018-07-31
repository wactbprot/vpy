import sys
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd
import tempfile
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.result import Result
from vpy.standard.se2.cal import Cal
from vpy.standard.se2.uncert import Uncert
from vpy.values import Values
from vpy.todo import ToDo

"""
Bsp. Aufruf:
python se2_calibration_mb.py --id "cal-2018-se2-pn-0118_0001" --db "vl_db_corr" --srv "http://i75422:5984"
python se2_calibration_mb.py --id "cal-2018-se2-kk-75001_0001" --db "vl_db" --srv "http://a73434:5984"
python se2_calibration_mb.py --id "cal-2018-se2-kk-75012_0001" --db "vl_db" --srv "http://a73434:5984"
python se2_calibration_mb.py --id "cal-2018-se2-kk-75043_0001" --db "vl_db" --srv "http://a73434:5984"
python se2_calibration_mb.py --id "cal-2018-se2-kk-75063_0001" --db "vl_db" --srv "http://a73434:5984"
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

    ## Bsp. Berechn. Kalibrierdruck, Unsicherh.
    cal.temperature_after(ana)
    cal.temperature_room(ana)
    cal.pressure_cal(ana)
    cal.pressure_ind(ana)
    cal.pressure_conversion_factor(ana)
    cal.pressure_offset(ana)
    cal.measurement_time(ana)
    unc.temperature_vessel(ana)
    res.reject_outliers_index(ana)
    res.make_main_maesurement_index(ana)
    res.make_pressure_range_index(ana)
    res.make_error_table(ana)
    res.make_formula_section(ana)
    res.fit_thermal_transpiration()

    # key = self.Pres.round_to_n(p_cal, 2)
    # p_cal = [np.mean(g.values.tolist()) for _, g in pd.DataFrame(p_cal).groupby(key)]

    #print(pd.Series(ana.pick("Pressure","cal","mbar")))
    #print(pd.DataFrame(ana.pick("Pressure","cal","mbar")).head())
    
    print("*******")
    p_cal = ana.pick("Pressure","cal","mbar")
    print("*******")
    res.ToDo.make_average_index(p_cal,"mbar")
    print(res.ToDo.average_index)
    io.save_doc(res.build_doc(dest="Result"))
    print(5<3<5)
    a=np.pi**50
    print(a)
    print(str(a))
    print(str(a).split("."))
    # for i in range(-9,4): print(val.round_to_sig_dig(1234*10**i,2))
    # for i in range(-9,4): print(val.round_to_sig_dig(10234*10**i,2))
    # for i in range(-2,8): print(val.round_to_sig_dig(a,i))
    print(val.round_to_sig_dig_array([123,456,789],2))
    print(val.round_to_uncertainty(a,0.097,2))
    print(val.round_to_uncertainty_array([123,456,789],[0.01,1,10],2))
    print(val.round_to_sig_dig(0,2))
    print(val.round_to_uncertainty(0.,0.01,2))
    print(doc["Calibration"]["CustomerObject"]["Class"])
    print(doc["Calibration"]["CustomerObject"]["Owner"]["Name"])
    print(doc["Calibration"]["ToDo"]["Name"])
    print(doc["Calibration"]["ToDo"]["Values"]["Pressure"]["Unit"])
    print(doc["Calibration"]["ToDo"]["Type"])
    print(val.unit_convert(5,"Torr","mbar"))
    print(val.unit_convert(5,"Torr"))
    print(val.unit_convert_array([1,2,3,4],"Torr"))
    print(val.unit_convert_array([1,2,3,4],"C"))
    print(val.unit_convert_array([1,2,3,4],"C","K"))
    print(val.unit_convert_array([1,2,3,4],"K","C"))
    print(ana.pick("Time","Date","date"))

if __name__ == "__main__":
    main()
