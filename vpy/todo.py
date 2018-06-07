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

        if "Values" in doc:
            if 'Pressure' in doc["Values"]:
                self.Pres = Pressure(doc["Values"])
                # delete pressure
                doc.pop('Pressure', None)

            if 'Temperature' in doc:
                self.Temp = Temperature(doc["Values"])
                # delete pressure
                doc.pop('Temperature', None)

        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))
