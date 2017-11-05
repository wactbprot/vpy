"""Script processes the already analysed file:
cal-2017-frs5|dkm_ppc4-ik-4050_0001
and
cal-2017-frs5|dkm_ppc4-ik-4050_0002
It generates the Interpol block in the CalibrationObjects:
cob-cdg-se3_1T_1 to cob-cdg-se3_1000T_3

The interpolation for the 100T CDGs uses values from
FRS5 and DKM Measurement.

The analysis of the FRS5 Pressure and DKM was made by R-script.

"""

import coloredlogs
import logging as log
import numpy as np
import argparse
import sys

from device.cdg import InfCdg
from values import  Pressure
from vpy_io import Io

if __name__ == "__main__":

    coloredlogs.install()

    io = Io()
    ## --id cal-2017-frs5|dkm_ppc4-ik-4050_0001
    doc = io.load_doc()

    ## 1T CDGs FRS5

    PFrs = Pressure(doc, "Analysis")

    ## --1--
    cdg_1T_1 = cdb.get_doc("cob-cdg-se3_1T_1")
    Cdg_1T_1 =  InfCdg(doc, cdg_1T_1)
    p, e     = Cdg_1T_1.cal_error_interpol(PFrs.get_value("1T_1-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    Cdg_1T_1.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_1T_1.get_all())
    ## --2--
    cdg_1T_2 = cdb.get_doc("cob-cdg-se3_1T_2")
    Cdg_1T_2 =  InfCdg(doc, cdg_1T_2)
    p, e     = Cdg_1T_2.cal_error_interpol(PFrs.get_value("1T_2-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    Cdg_1T_2.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_1T_2.get_all())
    ## --3--
    cdg_1T_3 = cdb.get_doc("cob-cdg-se3_1T_3")
    Cdg_1T_3 =  InfCdg(doc, cdg_1T_3)
    p, e     = Cdg_1T_3.cal_error_interpol(PFrs.get_value("1T_3-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    Cdg_1T_3.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_1T_3.get_all())

    ## 10T CDGs FRS5
    ## --1--
    cdg_10T_1 = cdb.get_doc("cob-cdg-se3_10T_1")
    Cdg_10T_1 =  InfCdg(doc, cdg_10T_1)
    p, e      = Cdg_10T_1.cal_error_interpol(PFrs.get_value("10T_1-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    Cdg_10T_1.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_10T_1.get_all())
    ## --2--
    cdg_10T_2 = cdb.get_doc("cob-cdg-se3_10T_2")
    Cdg_10T_2 =  InfCdg(doc, cdg_10T_2)
    p, e      = Cdg_10T_2.cal_error_interpol(PFrs.get_value("10T_2-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    Cdg_10T_2.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_10T_2.get_all())
    ## --3--
    cdg_10T_3 = cdb.get_doc("cob-cdg-se3_10T_3")
    Cdg_10T_3 =  InfCdg(doc, cdg_10T_3)
    p, e      = Cdg_10T_3.cal_error_interpol(PFrs.get_value("10T_3-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    Cdg_10T_3.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_10T_3.get_all())

    # 100T CDGs FRS5
    ## --1--
    cdg_100T_1 = cdb.get_doc("cob-cdg-se3_100T_1")
    Cdg_100T_1 =  InfCdg(doc, cdg_100T_1)
    pf1, ef1   = Cdg_100T_1.cal_error_interpol(PFrs.get_value("100T_1-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    ## --2--
    cdg_100T_2 = cdb.get_doc("cob-cdg-se3_100T_2")
    Cdg_100T_2 =  InfCdg(doc, cdg_100T_2)
    pf2, ef2   = Cdg_100T_2.cal_error_interpol(PFrs.get_value("100T_2-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")
    ## --3--
    cdg_100T_3 = cdb.get_doc("cob-cdg-se3_100T_3")
    Cdg_100T_3 =  InfCdg(doc, cdg_100T_3)
    pf3, ef3   = Cdg_100T_3.cal_error_interpol(PFrs.get_value("100T_3-ind_corr", "mbar"), PFrs.get_value("frs5", "mbar"), "mbar")

    ## 100T CDGs DKM
    doc = cdb.get_doc("cal-2017-frs5|dkm_ppc4-ik-4050_0002")
    PDkm = Pressure(doc, "Analysis")
    ## --1--
    pi1 = np.concatenate((PFrs.get_value("100T_1-ind_corr", "mbar"), PDkm.get_value("100T_1-ind_corr", "mbar")))
    pc1 = np.concatenate((PFrs.get_value("frs5"           , "mbar"), PDkm.get_value("dkmppc4"        , "mbar")))
    pd1, ed1 = Cdg_100T_1.cal_error_interpol(pi1, pc1, "mbar")
    Cdg_100T_1.store_error_interpol(pd1, ed1, "mbar", "1")
    cdb.set_doc(Cdg_100T_1.get_all())
    ## --2--
    pi2 = np.concatenate((PFrs.get_value("100T_2-ind_corr", "mbar"), PDkm.get_value("100T_2-ind_corr", "mbar")))
    pc2 = np.concatenate((PFrs.get_value("frs5"           , "mbar"), PDkm.get_value("dkmppc4"        , "mbar")))
    pd2, ed2 = Cdg_100T_2.cal_error_interpol(pi2, pc2, "mbar")
    Cdg_100T_2.store_error_interpol(pd2, ed2, "mbar", "1")
    cdb.set_doc(Cdg_100T_2.get_all())
    ## --3--
    pi3 = np.concatenate((PFrs.get_value("100T_3-ind_corr", "mbar"), PDkm.get_value("100T_3-ind_corr", "mbar")))
    pc3 = np.concatenate((PFrs.get_value("frs5"           , "mbar"), PDkm.get_value("dkmppc4"        , "mbar")))
    pd3, ed3 = Cdg_100T_3.cal_error_interpol(pi3, pc3, "mbar")
    Cdg_100T_3.store_error_interpol(pd3, ed3, "mbar", "1")
    cdb.set_doc(Cdg_100T_3.get_all())

    ## 1000T CDGs DKM
    ## --1--
    cdg_1000T_1 = cdb.get_doc("cob-cdg-se3_1000T_1")
    Cdg_1000T_1 =  InfCdg(doc, cdg_1000T_1)
    p, e        = Cdg_1000T_1.cal_error_interpol(PDkm.get_value("1000T_1-ind_corr", "mbar"), PDkm.get_value("dkmppc4", "mbar"), "mbar")
    Cdg_1000T_1.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_1000T_1.get_all())
    ## --2--
    cdg_1000T_2 = cdb.get_doc("cob-cdg-se3_1000T_2")
    Cdg_1000T_2 =  InfCdg(doc, cdg_1000T_2)
    p, e        = Cdg_1000T_2.cal_error_interpol(PDkm.get_value("1000T_2-ind_corr", "mbar"), PDkm.get_value("dkmppc4", "mbar"), "mbar")
    Cdg_1000T_2.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_1000T_2.get_all())
    ## --3--
    cdg_1000T_3 = cdb.get_doc("cob-cdg-se3_1000T_3")
    Cdg_1000T_3 =  InfCdg(doc, cdg_1000T_3)
    p, e        = Cdg_1000T_3.cal_error_interpol(PDkm.get_value("1000T_3-ind_corr", "mbar"), PDkm.get_value("dkmppc4", "mbar"), "mbar")
    Cdg_1000T_3.store_error_interpol(p, e, "mbar", "1")
    cdb.set_doc(Cdg_1000T_3.get_all())
