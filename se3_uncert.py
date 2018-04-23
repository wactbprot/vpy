from vpy.analysis import Analysis
from vpy.sim import Sim
from vpy.standard.se3.uncert import Uncert
from vpy.standard.se3.cal import Cal

def main():

    sim = Sim("se3")
    doc = sim.build()

    res = Analysis(doc)
    unc = Uncert(doc)
    cal = Cal(doc)

    cal.pressure_cal(res)
    unc.total(res)
    p = res.pick("Pressure", "cal", "mbar")
    u = res.pick("Uncertainty", "total", "1")*1.4
    
if __name__ == "__main__":
    main()
