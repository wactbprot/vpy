import sys
import os
#sys.path.append(os.environ["VIRTUAL_ENV"])

import json
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal


def main():
    io = Io()
    io.eval_args()
    doc = io.get_state_doc(name="se3")
    base_doc = io.get_base_doc(name="se3")

    for k, v in base_doc.items():
        doc['State'][k] = v

    cal = Cal(doc)
    res = Analysis(doc)

    cal.time_state(res)
    cal.volume_state(res)
    cal.pressure_state(res)
    cal.outgas_state(res)
    cal.pressure_loss(res)
    cal.temperature_state(res)

    chk = Analysis(res.build_doc())
    cal.check_state(res, chk)

    io.save_doc(chk.build_doc("Check"))

if __name__ == "__main__":
    main()
