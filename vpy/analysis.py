import datetime
import subprocess
import copy
import numpy as np
from .document import Document


class Analysis(Document):
    """Holds a deep copy of original document. Container for storing
    Results of analysis.
    """

    def __init__(self, doc):
        doc = copy.deepcopy(doc)
        d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        githash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode('ascii').strip()
        o = {"Date": [{
            "Type": "generated",
                    "Value": d}],
             "Values": {},
             "AnalysisProgram": "vpy",
             "AnalysisGitHash": githash
             }

        super().__init__(o)
        self.org = doc

    def store(self, quant, t, v, u, sd=None, n=None):
        """Stores the result of a calculation in
        the analysis structure below the given quantity.
        """

        v = self.make_writable(v)
        n = self.make_writable(n)
        sd = self.make_writable(sd)

        o = {"Type": t, "Value": v, "Unit": u}
        if sd is not None:
            o['SdValue'] = sd
        if n is not None:
            o['N'] = n

        if quant not in self.doc['Values']:
            self.doc['Values'][quant] = []

        self.doc['Values'][quant].append(o)
        self.log.info("stored values of type {} in {}".format(t, quant))

    def store_dict(self, quant, d):
        """ Appends complete dicts to document
        """
        for e in d:
            d[e] = self.make_writable(d[e])

        if quant not in self.doc['Values']:
            self.doc['Values'][quant] = []

        self.doc['Values'][quant].append(d)

    def make_writable(self, a):
        """ converts array, nd.array etc. to json writable lists
        """

        if "tolist" in dir(a):
            a = copy.deepcopy(a)
            #a[np.where(np.isnan(a))] = None
            a = a.tolist()

        return a

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
                    print("--##")
                    print(ret)
        else:
            self.log.error("{} not in Values".format(quant))

        return ret

    def build_doc(self, dest='Analysis'):
        """Merges the analysis dict to the original doc and returns it.

        :returns: assembled dictionary
        :rtype: dict
        """
        if "Calibration" in self.org:
            self.org['Calibration'][dest] = self.doc
        elif "State" in self.org:
            self.org['State'][dest] = self.doc
        else:
            self.org[dest] = self.doc

        return self.org
