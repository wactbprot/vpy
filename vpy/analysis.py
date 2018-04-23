import datetime
import copy
import numpy as np
from .document import Document

class Analysis(Document):
    """Holds a deep copy of original document. Container for storing
    Results of analysis.
    """
    def __init__(self, doc):
        doc = copy.deepcopy(doc)
        d   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        o   = {"Date":[{
                    "Type": "generated",
                    "Value": d}],
                    "Values":{}}
        super().__init__(o)
        self.org = doc
        self.log.debug("init func: {}".format(__name__))

    def store(self, quant, t, v, u, sd=None, n=None):
        """Stores the result of a calculation in
        the analysis structure below the given quantity.
        """

        if "tolist" in dir(v):
            v = copy.deepcopy(v)
            v[np.where(np.isnan(v))] = 0.0
            v = v.tolist()

        if "tolist" in dir(sd):
            sd = copy.deepcopy(sd)
            sd[np.where(np.isnan(sd))] = 0.0
            sd = sd.tolist()

        if "tolist" in dir(n):
            n = copy.deepcopy(n)
            n[np.where(np.isnan(n))] = 0.0
            n = n.tolist()

        o = {"Type":t, "Value":v, "Unit":u}
        if sd is not None:
            o['SdValue'] = sd
        if n is not None:
            o['N'] = n

        if quant not in self.doc['Values']:
            self.doc['Values'][quant] = []

        self.doc['Values'][quant].append(o)
        self.log.info("stored values of type {} in {}".format(t, quant))

    def pick(self, quant, val, unit):
        """Picks and returns an already calculated value.

        :param quant: quant measurement quantity
        :type quant: str

        :param val: value of type to pick
        :type val: str

        :param unit: unit expected
        :type unit: str
        """

        if quant in self.doc['Values']:
            doc = self.doc['Values'][quant]
            for d in doc:
                if d['Type'] == val:
                    ret = self.get_value(val, unit, d)
        else:
            self.log.error("{} not in Values".format(quant))

        return ret

    def build_doc(self):
        """Adds the analysis to the original doc and returns it.

        :returns: assembled dictionary
        :rtype: dict
        """
        if "Calibration" in self.org:
            self.org['Calibration']['Analysis'] = self.doc
        elif "State" in self.org:
            self.org['State']['Analysis'] = self.doc
        else:
            self.org['Analysis'] = self.doc

        return self.org
