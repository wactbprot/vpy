from vpy.analysis import Analysis
from vpy.sim import Sim
from vpy.standard.frs5.uncert import Uncert
from vpy.standard.frs5.cal import Cal

def main():

    sim = Sim("frs5")
    doc = sim.build()

    res = Analysis(doc)
    unc = Uncert(doc)
    cal = Cal(doc)

    cal.pressure_cal(res)
    unc.total(res)
    p = res.pick("Pressure", "frs5", "mbar")
    u = res.pick("Uncertainty", "frs5_total_rel", "1")
    print(p)
    print(u)


if __name__ == "__main__":
    main()
