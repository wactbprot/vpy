import copy
from log import log
from document import Document
from constants import Constants
from calibration_devices import  CalibrationObject

class Standard(Document):
    """Standard Class. Needs access to Constants, CalibrationObjects
    and measurement values.
    Provides the normals main measurand e.g. calibration pressure
    """

    log = log().getLogger(__name__)
    log.info("Document class ini")

    def __init__(self, orgdoc, name):
        doc = copy.deepcopy(orgdoc)

        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'Standard' in dc:
                dcs = dc['Standard']

            if isinstance(dcs, list):
                for s in dcs:
                    if s['Name'] == name:
                        super().__init__(s)

            if isinstance(dcs, dict):
                if dcs['Name'] == name:
                    super().__init__(dcs)

        if 'Standard' in doc:
            if doc['Standard']['Name'] == name:
                super().__init__(doc['Standard'])


        self.Cons = Constants(doc)
        self.Cobj = CalibrationObject(doc)

    def real_gas_correction(self, res):
        """Real gas correction for already calculated filling pressure
        """

        gas   = self.get_gas()
        B     = self.Cons.get_value("virialCoeff_" + gas, "cm^3/mol")
        T     = self.Cons.get_value("referenceTemperature", "K")

        vconv = self.Cons.get_conv("m^3", "cm^3")
        R     = self.Cons.get_value("R", "Pa m^3/mol/K") * vconv

        pconv = self.Cons.get_conv("mbar", "Pa")
        p     = res.pick("Pressure", "fill", "mbar") * pconv

        rg    = 1./(1. + p*B/(R*T))

        res.store("Correction", "rg", rg, "1")
