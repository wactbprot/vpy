import json
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal


def main():
    io = Io()
    doc = io.get_state_doc("se3")
    base_doc = io.get_base_doc("se3")

    for k, v in base_doc.items():
        doc['State'][k] = v

    cal = Cal(doc)
    res = Analysis(doc)

    cal.volume_add(res)
    cal.pressure_state(res)
    cal.outgas_rate(res)
    cal.temperatur_single(res)

    chk = Analysis(res.build_doc())
    cal.check(res, chk)
    io.save_doc(chk.build_doc("Check"))

if __name__ == "__main__":
    main()
