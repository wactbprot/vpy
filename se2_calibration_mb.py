import sys
import numpy as np
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
"""

def main():
    io = Io()
    # holt Messdaten aus --db
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
    unc.temperature_vessel(ana)
    res.reject_outliers_index(ana)

    def u_PTB_rel(p):
        return np.piecewise(p, [p <= 0.00027, p <= 0.003, p <= 0.0073, p <= 0.09, p <= 10, p <= 80,  80 < p],
            [0.0014, 0.001, 0.00092, 0.00086, 0.00075, 0.00019, 0.00014])

    def repeat_rel(p):
        return np.piecewise(p, [p <= 0.1, p <= 10, p > 10], [0.0008, 0.0003, 0.0001])

    # key = self.Pres.round_to_n(p_cal, 2)
    # p_cal = [np.mean(g.values.tolist()) for _, g in pd.DataFrame(p_cal).groupby(key)]

    # print(doc)
    print(ana.pick("Pressure","cal","mbar"))
    print(pd.Series(ana.pick("Pressure","cal","mbar")))
    print(pd.DataFrame(ana.pick("Pressure","cal","mbar")).head())
    print("*******")
    p_cal = ana.pick("Pressure","cal","mbar")
    print(np.std(p_cal))
    print(np.mean(p_cal))
    print(np.random.rand(2,3))
    print("*******")
    print(u_PTB_rel(0.001))
    print(p_cal)
    print(u_PTB_rel(p_cal))
    print(repeat_rel(p_cal))
    print("*******")
    print(ana.pick("Pressure","cal","mbar"))
    print(ana.pick("Pressure","ind","mbar"))
    print(Values.round_to_n(1,[3,4,5,0.1],1))
    # print([np.take(b, i).tolist() for i in r])
    res.ToDo.make_average_index(p_cal,"mbar")
    print(res.ToDo.average_index)
    print([1,2,3,4])

if __name__ == "__main__":
    main()
