import copy
from ..document import Document
from ..constants import Constants
from ..values import Values
from ..todo import ToDo
from ..calibration_devices import CalibrationObject


class Standard(Document):
    """All standards need ``Constants`` and ``CalibrationObjects``.
    ``Values({})`` provides many useful functions.
    """
    low_is_best = [0,1,2,3,4,5,6,7,8,9]
    high_is_best = [9,8,7,6,5,4,3,2,1,0]
    center_is_best = [8,6,4,2,0,1,3,5,7,9]
    between_is_ok = [9,4,2,0,0,0,0,2,4,9]
    all_bad = [9,9,9,9,9,9,9,9,9,9]

    rating_distributions = {'OutGasRate': low_is_best,
                            'PressureLoss':between_is_ok,
                            'Error':center_is_best,
                            'Pressure':center_is_best,
                            'Volume' : between_is_ok,
                            'Temperature': center_is_best,
                            'Fallback': all_bad,}

    def __init__(self, doc, name):

        self.Cons = Constants(doc)
        self.Cobj = CalibrationObject(doc)
        self.Vals = Values({})

        if 'State' in doc:
            doc = doc.get('State')

        if 'Calibration' in doc:
            doc = doc.get('Calibration')

        if "ToDo" in doc:
            self.ToDo = ToDo(doc)

        if 'Standard' in doc:
            doc = doc.get('Standard')

            if isinstance(doc, list):
                for s in doc:
                    if s.get('Name') == name:
                        super().__init__(s)

            if isinstance(doc, dict):
                if doc.get('Name') == name:
                    super().__init__(doc)

    def real_gas_correction(self, res):
        """Real gas correction for already calculated filling pressure
        """

        gas = self.get_gas()
        if gas is None:
            gas = self.ToDo.get_gas()
        B = self.Cons.get_value("virialCoeff_" + gas, "cm^3/mol")
        T = self.Cons.get_value("referenceTemperature", "K")

        vconv = self.Cons.get_conv("m^3", "cm^3")
        R = self.Cons.get_value("R", "Pa m^3/mol/K") * vconv

        p = res.pick("Pressure", "fill", self.unit)

        rg = 1. / (1. + p * B / (R * T))

        res.store("Correction", "rg", rg, "1")
