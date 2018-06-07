import sys
import numpy as np
from .document import Document


class Values(Document):
    """Values class implements special methodes for
    temperature, pressure ...

    :param doc: doc document
    :type doc: dict
    :param quant: quant part to search in e.g. Measurement, Analysis
    :type quant: str
    """

    def __init__(self, doc, name, quant):
        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'State' in doc:
            doc = doc['State']

        if quant in doc:
            doc = doc[quant]

        if 'Values' in doc:
            doc = doc['Values']

        if name in doc:
            super().__init__(doc[name])

        self.log.debug("init func: {}".format(__name__))

    def round_to_n(self, a, n):
        r=[]
        for x in a:
            if not x: return 0
            power = -int(np.floor(np.log10(abs(x)))) + (n - 1)
            factor = (10 ** power)
            r.append(round(x * factor) / factor)
        return np.asarray(r)

class Temperature(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Temperature', quant)


class Pressure(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Pressure', quant)


class OutGasRate(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'OutGasRate', quant)

class Position(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Position', quant)

class Time(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Time', quant)

    def get_rmt(self, val, unit):
        """Returns the relative measurement

        :param val: val of the Type (e.g. amt_fill)
        :type val: str
        :param unit: expected unit of the Type (e.g. ms)
        :type unit: str
        :returns: relative measure time
        :rtype: np.array | None
        """
        t = self.get_value(val, unit)

        if t is not None:
            t = t - t[0]

        return t


class AuxValues(Document):

    def __init__(self, doc):
        if 'Calibration' in doc:
            doc = doc['Calibration']

        if 'State' in doc:
            doc = doc['State']

        if 'Measurement' in doc:
            doc = doc['Measurement']

        if 'AuxValues' in doc:
            super().__init__(doc['AuxValues'])

    def get_gas(self):
        if "Gas" in self.doc:
            return self.doc['Gas']
        else:
            self.log.warn("Use default gas N2")
            return "N2"

    def get_by_time(self, meastime, auxtime, timeunit, auxval, valunit):
        """
        ..todo:: write a better description

        Some values are measured only a few times like offsets.
        Such values are stored below the ``AuxValues``-section.
        This Function implements a expansion mechanism
        and returns a array of the length ``len(meastime)``

        .. note:: The first measured offset is valid until the
                  second offset is measured.

        :param meastime: meastime array
        :type meastime: np.array

        :param auxtime: auxtime name of the time type to expand
        :type auxtime: str

        :param timeunit: timeunit unit of the type to expand
        :type timeunit: str

        :param auxval: auxval name of the type to expand
        :type auxval: str

        :param valunit: valunit unit of the type to expand
        :type valunit: str
        """

        N = len(meastime)
        ret = np.full(N, np.nan)
        time = self.get_value(auxtime, timeunit)
        value = self.get_value(auxval, valunit)
        if len(time) == len(value):
            i = 0
            for tm in meastime:
                j = 0
                for to in time:
                    if tm > to:
                        ret[i] = value[j]
                        j = j + 1
                i = i + 1

            self.log.debug("offset values expanded, will return")

            return ret
        else:
            err = """length of offset time vec does
            not match the length of values"""
            self.log.error(err)
            sys.exit(err)

    def get_val_by_time(self, meastime, auxtime, timeunit, auxval, valunit):
        return self.get_by_time(meastime, auxtime, timeunit, auxval, valunit)

    def get_obj_by_time(self, meastime, auxtime, timeunit, auxval, valunit):
        val = self.get_by_time(meastime, auxtime, timeunit, auxval, valunit)
        return {"Type": auxval, "Value":  val, "Unit": valunit}


class AuxSe3(AuxValues):
    """AuxValues for SE3 Standard.
    """

    def __init__(self, doc):
        super().__init__(doc)

    def get_expansion(self):
        """At documents concerned with certain
        expansions ratios  (e.g. expanson ratio measurements) the name of the
        investigated :math: f is stored in ``AuxValues.Expansion``

        :returns: name of the investigated expansion
        :rtype: str
        """
        if "Expansion" in self.doc:
            o = self.get_object("Type", "name")
            if "Value" in o:
                if isinstance(o['Value'], list):
                    return o['Value'][-1]
        else:
            self.log.info("Name of Expansion not available in AuxValues")
            return None

    def get_volume(self, t):
        """Returns additional volumes prev. measured (state documents)

        :param t: type of Volume (``abc``, ``bc`` or ``c``)
        :type doc: str
        :returns: name of the investigated expansion
        :rtype: str
        """
        if "Volume" in self.doc:
            v = self.get_value("add_{}".format(t), "cm^3")
        
        if v is not None:
            return v

class AuxSe2(AuxValues):
    """AuxValues for SE2 Standard.
    """

    def __init__(self, doc):
        super().__init__(doc)

    def get_expansion(self):
        """On the documents concerned with certain
        expansions ratios the name of the investigated :math: f
        is stored in AuxValues.Expansion

        :returns: name of the investigated expansion
        :rtype: str
        """
        if "Expansion" in self.doc:
            o = self.get_object("Type", "name")
            if "Value" in o:

                if isinstance(o['Value'], list):
                    return o['Value'][-1]
        else:
            self.log.info("Name of Expansion not available in AuxValues")
            return None


class AuxFrs5(AuxValues):
    """AuxValues for FRS5 Standard
    """

    def __init__(self, doc):
        super().__init__(doc)
