import copy
from ..document import Document
from ..constants import Constants
from ..todo import ToDo
from ..calibration_devices import CalibrationObject


class Standard(Document):
    """All standards need ``Constants`` and ``CalibrationObjects``
    """

    def __init__(self, doc, name):

        self.Cons = Constants(doc)
        self.Cobj = CalibrationObject(doc)

        if 'Calibration' in doc:
            doc = doc['Calibration']

        if "ToDo" in doc:
            self.ToDo = ToDo(doc)

        if 'State' in doc:
            doc = doc['State']

        if 'Standard' in doc:
            doc = doc['Standard']

            if isinstance(doc, list):
                for s in doc:
                    if s['Name'] == name:
                        super().__init__(s)

            if isinstance(doc, dict):
                if doc['Name'] == name:
                    super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

    def real_gas_correction(self, res):
        """Real gas correction for already calculated filling pressure
        """

        gas = self.get_gas()
        B = self.Cons.get_value("virialCoeff_" + gas, "cm^3/mol")
        T = self.Cons.get_value("referenceTemperature", "K")

        vconv = self.Cons.get_conv("m^3", "cm^3")
        R = self.Cons.get_value("R", "Pa m^3/mol/K") * vconv

        pconv = self.Cons.get_conv("mbar", "Pa")
        p = res.pick("Pressure", "fill", "mbar") * pconv

        rg = 1. / (1. + p * B / (R * T))

        res.store("Correction", "rg", rg, "1")
