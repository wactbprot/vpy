import sys
import os
import numpy as np
sys.path.append(os.environ["VIRTUAL_ENV"])
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal
from vpy.pkg_io import Io

def main():

    io = Io()
    io.eval_args()
    doc = {"_id": "se3-sim",
        "Calibration":{"Measurement":{}}}

    base_doc = io.get_base_doc("se3")
    doc = io.update_cal_doc(doc, base_doc)

    vals = io.read_json("./vpy/standard/se3/values_sim.json")
    aux_vals = io.read_json("./vpy/standard/se3/meas_aux_values.json")
    ana_aux_vals = io.read_json("./vpy/standard/se3/ana_aux_values.json")

    doc['Calibration']['Measurement']['Values'] = vals
    doc['Calibration']['Measurement']['AuxValues'] = aux_vals

    ana = Analysis(doc, insert_dict={'AuxValues': ana_aux_vals}, analysis_type="expansion")

    Cal(doc).all(ana)
    Uncert(doc).total(ana)

    io.save_doc(ana.build_doc())

if __name__ == "__main__":
    main()
