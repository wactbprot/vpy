import sys
import numpy as np
from .document import Document
from .values import Pressure, Temperature


class ToDo(Document):
    """Initialisation of ToDo class.

    :param doc: doc ToDo to search and extract
    :type doc: dict
    """

    def __init__(self, doc):

        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'ToDo' in doc:
            doc = doc['ToDo']

        super().__init__(doc)

        if 'Type' in doc:
            self.type = doc['Type']
        if 'Values' in doc:
            if 'Pressure' in doc['Values']:
                self.Pres = Pressure(doc['Values'])
                # delete pressure
                doc.pop('Pressure', None)

            if 'Temperature' in doc:
                self.Temp = Temperature(doc["Values"])
                # delete pressure
                doc.pop('Temperature', None)


        self.max_dev = 0.1
        self.log.debug("init func: {}".format(__name__))

    def make_average_index(self, cal, unit):
        """Generates and returns a numpy array containing
        the indices of measurement points which belong to a
        certain target pressure.

        :param cal: np array of values to group
        :type cal: np.array

        :param unit: unit of cal
        :type unit: str

        :returns: array of arrays of indices
        :rtype: np.array
        """

        target = self.Pres.get_value("target", unit)
        r = []
        for i in range(0, len(target)):
            rr = []
            for j in range(0, len(cal)):
                if abs(cal[j] / target[i] - 1) < self.max_dev:
                    rr.append(j)
            r.append(rr)

        self.average_index = r
