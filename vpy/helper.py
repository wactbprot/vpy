from vpy.device.srg import Srg
from vpy.device.cdg import Cdg
from vpy.device.rsg import Rsg
from vpy.device.qbs import Qbs
from vpy.device.ig import Ig
from vpy.device.pir import Pir
from vpy.values import Values
from vpy.analysis import Analysis

def init_customer_device(doc):
    customer_object = doc.get('Calibration').get('CustomerObject')

    if customer_object.get("Class") == "SRG":
        cus_dev = Srg(doc, customer_object)
    if customer_object.get("Class") == "CDG":
        cus_dev = Cdg(doc, customer_object)
    if customer_object.get("Class") == "RSG":
        cus_dev = Rsg(doc, customer_object)
    if customer_object.get("Class") == "QBS":
        cus_dev = Qbs(doc, customer_object)
    if customer_object.get("Class") == "IG":
        cus_dev = Ig(doc, customer_object)
    if customer_object.get("Class") == "PIR":
        cus_dev = Pir(doc, customer_object)

    return cus_dev

def result_analysis_init(doc):
    analysis = doc.get('Calibration').get('Analysis')
    ## keep standard uncertainty and clean the rest
    u_std = Values(analysis.get("Values").get("Uncertainty")).get_value("standard", "1")
    del analysis['Values']['Uncertainty']
    analysis_type = analysis.get("AnalysisType", "default")
    ana = Analysis(doc, init_dict=analysis, analysis_type=analysis_type)
    ana.store("Uncertainty", "standard", u_std, "1")

    return ana
