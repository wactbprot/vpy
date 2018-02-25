import sys
import numpy as np
from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.sim import Sim
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal

def main():
    io = Io()
    sim = Sim("se3")
    doc = sim.build()

    res = Analysis(doc)
    unc = Uncert(doc)
    cal = Cal(doc)

    cal.get_add_ratio(res)
    cal.pressure_fill(res)
    cal.temperature_before(res)
    cal.temperature_after(res)

    unc.total(res)


if __name__ == "__main__":
    main()
