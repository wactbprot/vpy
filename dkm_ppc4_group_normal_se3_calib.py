"""
Calculates the calibration pressure and
the error interpolation of the indicated pressure
 cal-2018-dkm_ppc4-ik-4050_0001

"""

from vpy.pkg_io import Io
from vpy.analysis import Analysis
from vpy.standard.dkm_ppc4.cal import Cal
from vpy.device.cdg import InfCdg

def main():
    io = Io()
    doc = io.load_doc()

    res = Analysis(doc)

    cal = Cal(doc)
    cal.pressure_cal(res)
    heads = ["100T_1","100T_2","100T_3","1000T_1","1000T_2","1000T_3"]
    p_cal = res.pick("Pressure", "cal", "mbar")
    m_time = cal.Time.get_value("amt_meas", "ms")

    for head in heads:

        p_off = cal.Aux.get_val_by_time(
            m_time, "offset_mt", "ms", "{}-ind_offset".format(head), "mbar")
        p_ind = cal.Pres.get_value("{}-ind".format(head), "mbar")

        cdg_doc = io.get_doc_db("cob-cdg-se3_{}".format(head))
        Cdg = InfCdg(doc, cdg_doc)
        p, e = Cdg.cal_error_interpol(p_ind - p_off, p_cal, "mbar")
    
        Cdg.store_error_interpol(p, e, "mbar", "1")
        io.set_doc_db(Cdg.get_all())



if __name__ == "__main__":
    main()
