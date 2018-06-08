import sys
import numpy as np
from .document import Document
from .values import Pressure, Temperature

class ToDo(Document):
    """Initialisation of ToDo class.

    :param doc: doc ToDo to search and extract
    :type doc: dict
    """
    head_cell = {'cal' : "{\\(p_{cal}\\)}",
            'ind' : "{\\(p_{ind}\\)}",
            "uncertTotal_rel" :"{\\(U(k=2)\\)}"
            }

    def __init__(self, doc):

        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'ToDo' in doc:
            doc = doc['ToDo']

        if 'Values' in doc:
            if 'Pressure' in doc['Values']:
                self.Pres = Pressure(doc['Values'])
                # delete pressure
                doc.pop('Pressure', None)

            if 'Temperature' in doc:
                self.Temp = Temperature(doc["Values"])
                # delete pressure
                doc.pop('Temperature', None)

        if 'Table' in doc:
            doc = doc['Table']
            for m in doc:# m .. z.B. Pressure
                for entr in doc[m]: # entr .. z.B. {Type: cal, Unit: mbar}
                    if entr['Type'] in self.head_cell:
                        entr['HeadCell'] = self.head_cell[ entr['Type'] ]
                    else:
                        pass
                        #sys.exit('missing head cell entry')
            print(doc)

        self.max_dev = 0.1
        # print(a)
        # print(b)
        # print(r)
        # print([np.take(b, i).tolist() for i in r])

        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

        def get_average_index(self, b, unit):
            """Generates and returns a numpy array containing
            the indices of measurement points which belong to a
            certain target pressure.

            :param p: np array of values to compare
            :type p: np.array

            :param unit: unit of p
            :type unit: str

            :returns: array of arrays of indices
            :rtype: np.array
            """

            a = self.Pres.get_value("target", unit)
            r = []
            for i in range(0, len(a)-1):
                rr = []
                for j in range(0, len(b)-1):
                    if abs(b[j]/a[i]-1) < self.max_dev:
                        rr.append(j)
                r.append(rr)

            return np.asarray(r)
