import sys
import numpy as np
from .document import Document
from .values import Pressure, Temperature


class ToDo(Document):
    """Initialisation of ToDo class.

    :param doc: doc ToDo to search and extract
    :type doc: dict
    """
    max_dev = 0.05
    def __init__(self, doc):

        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'ToDo' in doc:
            doc = doc['ToDo']

        super().__init__(doc)

        if 'Type' in doc:
            self.type = doc.get('Type')
            if self.type == "srg_sigma":
                self.type = "sigma"

        if 'Values' in doc:
            values = doc.get('Values')
            if 'Pressure' in values:
                self.Pres = Pressure(values)
                self.pressure_unit = self.Pres.get_dict('Type', 'target').get('Unit')
                # delete pressure
                doc.pop('Pressure', None)

            if 'Temperature' in values:
                self.Temp = Temperature(values)
                self.temperature_unit = self.Temp.get_dict('Type', 'target').get('Unit')
                # delete temperature
                doc.pop('Temperature', None)

    def get_standard(self):
        return self.doc.get("Standard")

    def get_gas(self):
        return self.doc.get('Gas')

    def get_min_max_pressure(self):
        if "Pres" in dir(self):
            target_pressures = self.Pres.get_value("target", self.pressure_unit)
            if len(target_pressures) > 0:
                return float(target_pressures[0]), float(target_pressures[-1]),  self.pressure_unit
            else:
                 return np.nan, np.nan, self.pressure_unit
        else:
            return None, None, None

    def make_average_index(self, cal, unit, max_dev=None):
        """Generates and returns a numpy array containing
        the indices of measurement points which belong to a
        certain target pressure. The unit of the calibration
        pressure should be the same as ``self.pressure_unit``.

        :param cal: np array of values to group
        :type cal: np.array

        :param unit: unit of cal
        :type unit: str

        :returns: array of arrays of indices
        :rtype: np.array
        """

        target = self.Pres.get_value("target", unit)
        r = []
        if max_dev is None:
            max_dev = self.max_dev

        for i in range(0, len(target)):
            rr = []
            for j in range(0, len(cal)):
                if abs(cal[j] / target[i] - 1) < max_dev:
                    rr.append(j)
            r.append(rr)

        self.average_index = r
        return r

    def shape_pressure(self, min_p, max_p, unit):
        """Generates and returns a dict with pressures
        between the given min and max. The unit
        must be the same as self.pressure_unit.

        :param min: minimal pressure
        :type cal: float

        :param max: maximal pressure
        :type unit: float

        :param unit: pressure unit
        :type unit: str

        :returns: Type, Value, Unit, N dict
        :rtype: dict
        """

        pressure_dict = self.Pres.get_dict(key="Type", value="target")
        p = pressure_dict.get("Value")
        n = pressure_dict.get("N", [1]*len(p))
        u = pressure_dict.get("Unit")

        if u == unit:
            # zip(*l) is ugly,
            red_p = [ p[i] for i, v in enumerate(p) if max_p >= float(v) >= min_p]
            red_n = [ n[i] for i, v in enumerate(p) if max_p >= float(v) >= min_p]

            rest_p = [ p[i] for i, v in enumerate(p) if max_p < float(v)]
            rest_n = [ n[i] for i, v in enumerate(p) if max_p < float(v)]

            red_d = {"Type":"target", "Value":red_p, "N":red_n, "Unit":unit}

            if len(rest_p) > 0:
                return red_d, {"Type":"target", "Value":rest_p, "N":rest_n, "Unit":unit}
            else:
                return red_d, None

        else:
            sys.exit("units don't match on attempt to shape pressure")
