import json
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.se3.cal import Cal


def main():
    io       = Io()
    doc      = io.get_state_meas_doc("se3")
    base_doc = io.get_base_doc("se3")
    doc.update(base_doc)

    cal = Cal(doc)
    res = Analysis(doc)

    cal.volume_add(res)

    print(res.pick("Volume", "add_a", "cm^3"))
    print(res.pick("Volume", "add_ab", "cm^3"))
    print(res.pick("Volume", "add_abc", "cm^3"))

if __name__ == "__main__":
    main()
