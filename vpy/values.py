import sys
import re
import locale
import numpy as np
import time
from .document import Document


class Values(Document):
    """Values class implements special methodes for
    temperature, pressure ...

    :param doc: doc document
    :type doc: dict
    :param quant: quant part to search in e.g. Measurement, Analysis
    :type quant: str
    """

    def __init__(self, doc, name = None, quant = None):
        
        if name is None and quant is None:
            super().__init__(doc)
        else:
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

    def unit_convert(self, a, b="1"):
        """Returns conversion factor from unit a to unit b. Returns
        conversion factor to SI units if no second argument is given.

        :param a: initial unit
        :type a: str
        :param b: target unit
        :type b: str
        :returns: conversion factor
        :rtype: float
        """
        to_SI = {
            "1": 1,
            "%": 0.01,
            "mbar": 100,
            "Pa": 1,
            "Torr": 133.322
            }
        return to_SI[a]/to_SI[b]
    
    def round_to_sig_dig(self, val, n):
        """ Rounds the value ``val`` to ``n`` significant digits
        and outputs a formated string

        :param val: value to be rounded
        :type val: float
        :param n: number of significant digits
        :type n: integer       
        :returns: formated string
        :rtype: str
        """
        if not np.isfinite(val): return "nan"
        if n < 0: n = 0
        if val == 0: return f"{0:.{n - 1}f}"
        else:
            val_power = int(np.floor(np.log10(abs(val))))
            power = - val_power + (n - 1)
            factor = (10 ** power)
            val = round(val * factor) / factor
        if -3 <= val_power < 0: return f"{val:.{n - val_power - 1}f}"
        if  0 <= val_power < 5:
            n = n - val_power - 1
            if n < 0: n = 0
            return f"{val:.{n}f}"
        n = n - 1
        if n < 0: n = 0
        return f"{val:.{n}e}"

    def round_to_sig_dig_array(self, val_arr, n):
        """ Applies ``round_to_sig_dig`` to the array ``val_arr``
        """
        return np.asarray([self.round_to_sig_dig(i, n) for i in val_arr])

    def round_to_uncertainty(self, val, unc, n):
        """ Rounds the value ``val`` to the ``n``th significant digit
        of its uncertainty ``unc`` and outputs a formated string

        :param val: value to be rounded
        :type val: float
        :param unc: uncertainty of the value
        :type unc: float       
        :param n: number of significant digits of uncertainty
        :type n: integer       
        :returns: formated string
        :rtype: str
        """
        if not np.isfinite(val) or not np.isfinite(unc) or unc == 0: return "nan"
        if val == 0: val_power = 0
        else: val_power = int(np.floor(np.log10(abs(val))))
        unc_power = int(np.floor(np.log10(abs(unc))))
        n = val_power - unc_power + n
        return self.round_to_sig_dig(val, n)

    def round_to_uncertainty_array(self, val_arr, unc_arr, n):
        """ Applies ``round_to_uncertainty`` to the array of values ``val_arr``
        using the array of uncertainties ``unc_arr``
        """
        return np.asarray([self.round_to_uncertainty(val_arr[i], unc_arr[i], n) for i in range(len(val_arr))])
    
class Mass(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Mass', quant)

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

    def get_rmt(self, type, unit):
        """Returns the relative measurement.

        :param type: name of the Type (e.g. amt_fill)
        :type type: str
        :param unit: expected unit of the Type (e.g. ms)
        :type unit: str
        :returns: relative measure time
        :rtype: np.array | None
        """
        val = self.get_value(type, unit)

        if val is not None:
            val = val - val[0]

        return val

class Date(Values):
    def __init__(self, doc, quant="Measurement"):
        #super().__init__(doc, 'Date', quant)
        super().__init__(doc["Calibration"]["Measurement"]["Values"])

    def parse_labview_date(self):
        """Parses dates generated by LabView with the form:
        ``Mi, Mai 30, 2018``
        To match such a date ``locale.getlocale()`` has to be ``de_DE``

        .. todo::
            Does not work on windows system:  This:
            ``locale.setlocale(locale.LC_TIME, "")``
            works on unix; on windows too?
            (see https://www.python-forum.de/viewtopic.php?t=9906)

        :param t: name of the Type (e.g. amt_fill)
        :type t: str
        """
        locale.setlocale(locale.LC_TIME, "")
        val1 = self.get_str("Date")
        #val2 = self.get_all()["Time"]["Value"]
        #val = [val1[i] + "T" + val2[i] for i in range(len(val1))]
        val = [time.mktime(time.strptime(i, "%Y-%m-%d")) for i in val1]

        # p = re.compile('^[A-Z]{1}[a-z]{1}, [A-Z]{1}[a-z]{2} [0-3]{1}[0-9]{1}, [0-9]{4}$')
        # r =[]
        # for i in val:
        #    m = p.match(i)
        #    if m:
        #        t = time.mktime(time.strptime(i, '%a, %b %d, %Y'))
        #    else:
        #        t = np.nan

        #    r.append(t)

        return np.asarray(val)

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

class AuxDkmPpc4(AuxValues):
    """AuxValues for DKM_PPC4 Standard
    """

    def __init__(self, doc):
        super().__init__(doc)
