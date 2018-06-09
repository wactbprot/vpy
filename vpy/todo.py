import sys
import numpy as np
from .document import Document
from .values import Pressure, Temperature


class ToDo(Document):
    """Initialisation of ToDo class.

    :param doc: doc ToDo to search and extract
    :type doc: dict
    """
    head_cell = {'cal': "{\\(p_{cal}\\)}",
                 'ind': "{\\(p_{ind}\\)}",
                 "uncertTotal_rel": "{\\(U(k=2)\\)}"
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
            tbl = doc['Table']
            for m in tbl:  # m .. z.B. Pressure
                for entr in tbl[m]:  # entr .. z.B. {Type: cal, Unit: mbar}
                    if entr['Type'] in self.head_cell:
                        entr['HeadCell'] = self.head_cell[entr['Type']]
                        entr['UnitCell'] = entr['Unit'] # in case of specials
                    else:
                        pass
                        #sys.exit('missing head cell entry')


        self.max_dev = 0.1
        super().__init__(doc)

        # print(a)
        # print(b)
        # print(r)
        # print([np.take(b, i).tolist() for i in r])


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
        for i in range(0, len(target) - 1):
            rr = []
            for j in range(0, len(cal) - 1):
                if abs(cal[j] / target[i] - 1) < self.max_dev:
                    rr.append(j)
            r.append(rr)

        self.average_index = np.asarray(r)
