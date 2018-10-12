import datetime
import sys
import subprocess
import copy
import numpy as np
from .document import Document


class Analysis(Document):
    """Holds a deep copy of ``document``. Container for storing
    Results of analysis.
    """

    def __init__(self, doc, init_dict=None):

        if init_dict is None:
            d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            githash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode('ascii').strip()
            init_dict = {
                        "Date": [{
                        "Type": "generated",
                        "Value": d}],
                        "AuxValues":{
                            "AnalysisProgram": "vpy",
                            "AnalysisGitHash": githash
                        },
                        "Values": {},
                        }

        super().__init__(init_dict)
        self.org = copy.deepcopy(doc)

    def store(self, quant, type, value, unit, sd=None, n=None, dest='Values'):
        """Stores the result of a calculation in
        the analysis structure under the given quant[ity].

        :param quant: quant measurement quantity (Pressure, Temperature ect)
        :type quant: str

        :param type: name of type to store
        :type val: str

        :param value: value of type to store
        :type val: np.array

        :param unit: name of unit to store
        :type val: str

        :param sd:  standard deviation of the single values (optional)
        :type sd: np.array

        :param n:  n of the single values (optional)
        :type np: np.array

        :param dest:  destination (default in Values)
        :type str: str
        """

        value = self.make_writable(value)

        o = {"Type": type, "Value": value, "Unit": unit}
        if sd is not None:
            o['SdValue'] = self.make_writable(sd)

        if n is not None:
            o['N'] = self.make_writable(n)

        if dest is not None:
            if quant not in self.doc[dest]:
                self.doc[dest][quant] = []

            self.doc[dest][quant].append(o)
            self.log.info("stored values of type {} in {}".format(type, quant))
        else:
            if quant not in self.doc:
                self.doc[quant] = []

            self.doc[quant].append(o)
            self.log.info("stored values of type {}".format(type))

    def store_dict(self, quant, d, dest='Values', plain=False):
        """ Appends complete dicts to document under the given destination.


        :param quant: quant measurement quantity (Pressure, Temperature, ect)
        :type quant: str

        :param d: dictionary to store
        :type d: dict

        :param dest:  destination (default in Values)
        :type str: str

        :param plain:  if True stores dict w/o creating an array
        :type str: bool

        """
        if isinstance(d, dict):
            for e in d:
                d[e] = self.make_writable(d[e])

            if plain:
                if dest is not None:
                    self.doc[dest][quant] = d
                else:
                    self.doc[quant] = d
            else:
                if dest is not None:
                    if quant not in self.doc[dest]:
                        self.doc[dest][quant] = []
                    self.doc[dest][quant].append(d)
                else:
                    if quant not in self.doc:
                        self.doc[quant] = []
                    self.doc[quant].append(d)
        else:
            msg = "given value is not a dictionary"
            self.log.error(msg)
            sys.exit(msg)

    def make_writable(self, a):
        """ converts array, nd.array etc. to json writable lists
        """

        if "tolist" in dir(a):
            a = copy.deepcopy(a)
            self.log.debug("try to make: {} writable".format(a))
            odx = np.isnan(a)
            self.log.debug("odx: {}".format(odx))
            idx = np.where(odx)
            self.log.debug("idx: {}".format(idx))
            if np.shape(idx)[1] > 0:
                a[idx] = None
            a = a.tolist()

        return a
    
    def pick_dict(self, quant, dict_type, dest='Values'):
        """Picks and returns an already calculated value.

        :param quant: quant measurement quantity
        :type quant: str

        :param dict_type: value of type to pick
        :type dict_type: str

        :param dict_unit: dict_unit expected
        :type dict_unit: str
        """
        ret = None
        if dest in self.doc:
            if quant in self.doc[dest]:
                doc = self.doc[dest][quant]
                for d in doc:
                    if d['Type'] == dict_type:
                        ret = d
                        break
            else:
                msg = "{} not in Values".format(quant)
                self.log.error(msg)
                sys.exit(msg)
        else:
            msg = "{} not in self.doc".format(dest)            
            self.log.error(msg)
            sys.exit(msg)
        
        if ret is None:
            msg = "dict with type {} not found".format(dict_type)
            self.log.error(msg)
            sys.exit(msg)
        else:
            return ret

    def pick(self, quant, dict_type, dict_unit, dest='Values'):
        """Picks and returns an already calculated value.

        :param quant: quant measurement quantity
        :type quant: str

        :param dict_type: value of type to pick
        :type dict_type: str

        :param dict_unit: dict_unit expected
        :type dict_unit: str
        """
        res = None
        if dest in self.doc:
            if quant in self.doc[dest]:
                doc = self.doc[dest][quant]
                for d in doc:
                    if d['Type'] == dict_type:
                        ret = self.get_value(dict_type, dict_unit, d)
            else:
                msg = "{} not in Values".format(quant)
                self.log.error(msg)
                sys.exit(msg)
        else:
            msg = "{} not in self.doc".format(dest)            
            self.log.error(msg)
            sys.exit(msg)

        if ret is None: 
            msg = "dict with type {} not found".format(dict_type)
            self.log.error(msg)
            sys.exit(msg)
        else:
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
