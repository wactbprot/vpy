import pandas as pd
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

    p_f = ['{:.1e}'.format(i) for i in p]
    u_f = ['{:.1e}'.format(i) for i in u]
    df = pd.DataFrame({"$p_{cal}$ in mbar":p_f, "$u(k=1)$ (relative)":u_f})

    print(df.to_latex())
if __name__ == "__main__":
    main()
