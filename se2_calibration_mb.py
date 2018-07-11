import sys
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd
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

    # Berechnungen-Klasse leitet vom Standard se2 ab
    cal = Cal(doc)
    # Unsicherheits-Klasse leitet auch vom Standard se2 ab
    unc = Uncert(doc)

    ## Bsp. Berechn. Kalibrierdruck, Unsicherh.
    cal.pressure_cal(ana)
    cal.pressure_ind(ana)
    cal.pressure_offset(ana)
    cal.measurement_time(ana)
    unc.temperature_vessel(ana)
    res.reject_outliers_index(ana)
    res.make_offset_uncert(ana)
    res.make_error_table(ana)

    # key = self.Pres.round_to_n(p_cal, 2)
    # p_cal = [np.mean(g.values.tolist()) for _, g in pd.DataFrame(p_cal).groupby(key)]

    #print(pd.Series(ana.pick("Pressure","cal","mbar")))
    #print(pd.DataFrame(ana.pick("Pressure","cal","mbar")).head())
    
    print("*******")
    p_cal = ana.pick("Pressure","cal","mbar")
    print("*******")
    print(Values.round_to_n(1,[3,4,5,0.1],1))
    res.ToDo.make_average_index(p_cal,"mbar")
    print(res.ToDo.average_index)
    print(res.offset_uncert)
"""     print(len(res.pick("Pressure","p_cal","mbar")))
    print(len(res.pick("Pressure","p_ind","mbar")))
    print(len(res.pick("Error","e","%")))
    print(len(res.pick("Uncertainty","U","%"))) """

if __name__ == "__main__":
    main()
