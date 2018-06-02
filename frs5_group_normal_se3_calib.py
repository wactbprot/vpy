"""
Calculates the calibration pressure and
the error interpolation of the indicated pressure
``cal-2018-dkm_ppc4-ik-4050_0001``

The document
cal-2017-dkm_ppc4-ik-4050_0001
is a duplicate of
cal-2017-frs5|dkm_ppc4-ik-4050_0002

"""

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.frs5.cal import Cal
from vpy.standard.frs5.uncert import Uncert
from vpy.device.cdg import InfCdg

def main():
    io = Io()
    doc = io.load_doc()

    res = Analysis(doc)
    cal = Cal(doc)
    uncert = Uncert(doc)

    cal.pressure_cal(res)
    uncert.total(res)

    heads = ["1T_1","1T_2","1T_3",
            "10T_1","10T_2","10T_3",
            "100T_1","100T_2","100T_3"]

    p_cal = res.pick("Pressure", "frs5", "mbar")
    u_std = res.pick("Uncertainty", "frs5_total_rel", "1")

    m_time = cal.Time.get_value("amt_meas", "ms")

    for head in heads:

        p_off = cal.Aux.get_val_by_time(
            m_time, "offset_mt", "ms", "{}-ind_offset".format(head), "mbar")
        p_ind = cal.Pres.get_value("{}-ind".format(head), "mbar")

        cdg_doc = io.get_doc_db("cob-cdg-se3_{}".format(head))
        cdg = InfCdg(doc, cdg_doc)


        p, e, u = cdg.cal_interpol( p_cal, p_ind - p_off, u_std)
        u_cdg = cdg.get_total_uncert(p, "mbar", "mbar")/p

        cdg.store_interpol(p, e, (u**2 + u_cdg**2)**0.5,  "mbar", "1", "1")
        
        io.set_doc_db(cdg.get_all())

if __name__ == "__main__":
    main()
