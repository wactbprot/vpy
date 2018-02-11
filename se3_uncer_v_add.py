import sys
import numpy as np

from vpy.analysis import Analysis
from vpy.sim import Sim

from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal

def main():
    sim = Sim("se3")
    doc = sim.build()

    uncert = Uncert(doc)
    cal    = Cal(doc)
    res    = Analysis(doc)

    cal.temperature_before(res)
    #cal.temperature_after(res)
    #cal.temperature_room(res)
    #cal.pressure_fill(res)

if __name__ == "__main__":
    main()
