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

        doc1 = doc

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

        self.Pres2 = Pressure(doc1['Measurement'])
    
        a = self.Pres.get_value("target", "mbar").astype(np.float)
        b = self.Pres2.get_value("p_cal", " mbar")
        r = []
        for i in range(0, len(a)-1):
            rr = []
            for j in range(0, len(b)-1):                
                if abs(b[j]/a[i]-1) < 0.1:
                    rr.append(j)    
            r.append(rr)
        self.AvrIndexList = r

        # print(a)
        # print(b)
        # print(r)
        # print([np.take(b, i).tolist() for i in r])

        super().__init__(doc)

        self.log.debug("init func: {}".format(__name__))

