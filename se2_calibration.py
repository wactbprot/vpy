import sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se2.cal import Cal
from vpy.standard.se2.uncert import Uncert

"""
Bsp. Aufruf:
python se2_calibration.py --id 'cal-2018-se2-pn-0118_0001' --log d --db 'vl_db_corr' --srv 'http://i75422:5984'
"""

def main():
    io = Io()
    # holt Messdaten aus --db
    meas_doc = io.load_doc()
    # holt Konstanten ect. aus --db
    base_doc = io.get_base_doc("se2")
    # merge der beiden Dokumente
    doc = io.update_cal_doc(meas_doc, base_doc)
    res = Analysis(doc)

    # Berechnungen-Klasse leitet vom Standard se2 ab
    cal = Cal(doc)
    # Unsicherheits-Klasse leitet auch vom Standard se2 ab
    unc = Uncert(doc)

    ## Bsp. Berechn. Kalibrierdruck, Unsicherh.
    cal.pressure_cal(res)
    unc.temperature_vessel(res)

if __name__ == "__main__":
    main()
