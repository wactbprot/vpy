import sys
import numpy as np
from .vpy_io import Io
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
            dc = doc['Calibration']
            if quant in dc:
                dcm = dc[quant]
                if 'Values' in dcm:
                    dcmv = dcm['Values']
                    if name in dcmv:
                        super().__init__(dcmv[name])

        if name in doc:
            super().__init__(doc[name])

        self.log.debug("init func: {}".format(__name__))

class Temperature(Values):
    def __init__(self, doc, quant = "Measurement"):
        super().__init__(doc, 'Temperature', quant)

class Pressure(Values):
    def __init__(self, doc, quant = "Measurement"):
        super().__init__(doc,'Pressure', quant)

class Time(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Time', quant)

class AuxValues(Document):

    def __init__(self, doc):
        if 'Calibration' in doc:
            dc = doc['Calibration']
            if 'Measurement' in dc:
                dcm = dc['Measurement']
                if 'AuxValues' in dcm:
                    super().__init__(dcm['AuxValues'])

        if "AuxValues" in doc:
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

        N     = len(meastime)
        ret   = np.full(N, np.nan)
        time  = self.get_value(auxtime, timeunit)
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
        return  self.get_by_time(meastime, auxtime, timeunit, auxval, valunit)

    def get_obj_by_time(self, meastime, auxtime, timeunit, auxval, valunit):
        val = self.get_by_time(meastime, auxtime, timeunit, auxval, valunit)
        return {"Type": auxval, "Value":  val, "Unit":valunit}

class AuxSe3(AuxValues):
    """AuxValues for SE3 Standard.
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

class AuxSe2(AuxValues):
    """AuxValues for SE3 Standard.
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
