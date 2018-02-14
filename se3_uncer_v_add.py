import sys
import numpy as np

from vpy.analysis import Analysis
from vpy.sim import Sim

from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal

def main():
    sim = Sim("se3")
    doc = sim.build()
    
    res = Analysis(doc)
    cal = Cal(doc)
    unc = Uncert(doc)

    cal.pressure_fill(res)

if __name__ == "__main__":
    main()
