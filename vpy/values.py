import sys
import re
import locale
import numpy as np
import time
from datetime import datetime
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
            if 'State' in doc:
                doc = doc['State']
            if 'Calibration' in doc:
                doc = doc['Calibration']
            if quant in doc:
                doc = doc[quant]
            if name in doc: # works e.g. for Date
                super().__init__(doc[name])
            else: # we have to dig deeper for Pressure etc.
                if 'Values' in doc:
                    doc = doc['Values']
                if name in doc:
                    super().__init__(doc[name])
                else:
                    super().__init__({})
    
   
    def unit_convert(self, val, a, b="1"):
        """Returns value (or numpy array of values) converted from unit a to unit b.
        Returns value in SI units if no third argument is given.

        :param val: value (or numpy array of values) to be converted
        :type a: float (or numpy array of floats)
        :param a: initial unit
        :type a: str
        :param b: target unit
        :type b: str
        :returns: conversion factor
        :rtype: float
        """
        to_SI = {
            "1": val*1,
            "%": val*0.01,
            "C": val+273.15,
            "K": val,
            "mbar": val*100,
            "Pa": val*1,
            "Torr": val*133.322
            }
        val = to_SI[a]
        to_target_unit = {
            "1": val/1,
            "%": val/0.01,
            "C": val-273.15,
            "K": val,
            "mbar": val/100,
            "Pa": val/1,
            "Torr": val/133.322
            }
        return to_target_unit[b]

    def cnt_nan(self, d):
        return np.count_nonzero(~np.isnan(d))

    def gatherby_idx(self, l, compare_function):
        groups = {}
        for i in range(len(l)):
            for j in groups:
                if compare_function(l[i], l[j]):
                    groups[j].append(i)
                    break
            else: groups[i] = [i]
        return list(groups.values())
    
    def diff_less(self, d):
        return lambda x, y: abs(x-y)/((x+y)/2)<d

    def round_to_sig_dig(self, val, n, scientific=False):
        """ Rounds the value ``val`` to ``n`` significant digits
        and outputs a formated string

        :param val: value to be rounded
        :type val: float
        :param n: number of significant digits
        :type n: integer
        :returns: formated string
        :rtype: str
        """
        #check if val is a number
        if not np.isfinite(val): return "nan"

        #check if val is exactly zero
        if not(val == 0):                            
            #determine exponent of val to basis 10
            val_power = int(np.floor(np.log10(abs(val))))
            #round val by generating an integer with digits matching the number significant digits
            power = - val_power + (n - 1)
            factor = (10 ** power)
            val = round(val * factor) / factor
        else:
            val_power = 0

        #check if val is exactly zero after rounding
        #(because formating is then not handled satisfactorily by python)
        if val == 0:
            if not(scientific):
                if 0 < n - val_power:
                    return f"{0:.{n - val_power - 1}f}"
                else:
                    return "0"
            val_str = "0e"
            if - n + val_power +1 < 0:
                val_str = val_str + "-"
            else:
                 val_str = val_str + "+"
            if abs(- n + val_power +1) < 10:
                val_str = val_str + "0"
            return val_str + str(abs(- n + val_power +1))

        #if val is not exactly zero and scientific notation is switched off   
        if not(scientific) and val_power < 0: return f"{val:.{n - val_power - 1}f}"
        if not(scientific) and 0 <= val_power:
            n = n - val_power - 1
            if n < 0: n = 0
            return f"{val:.{n}f}"
            
        #in cases of scientific notation
        n = n - 1
        if n < 0: n = 0
        return f"{val:.{n}e}"


    def round_to_sig_dig_array(self, val_arr, n, scientific=False):
        """ Applies ``round_to_sig_dig`` to the array ``val_arr``
        """
        return np.asarray([self.round_to_sig_dig(i, n, scientific) for i in val_arr])


    def round_to_uncertainty(self, val, unc, n, scientific=False):
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

        return self.round_to_sig_dig(val, n, scientific)


    def round_to_uncertainty_array(self, val_arr, unc_arr, n, scientific=False):
        """ Applies ``round_to_uncertainty`` to the array of values ``val_arr``
        using the array of uncertainties ``unc_arr``
        """
        return np.asarray([self.round_to_uncertainty(val_arr[i], unc_arr[i], n, scientific) for i in range(len(val_arr))])

    def invers_array_sum(self, a):
        """Calculates the invers sum of columns the given array.
        
        .. code ::
            
            invers_array_sum([
                            [a1, a2, a3],
                            [b1, b2, b3]
                        ]) = 1/[1/a1 +1/b1, 1/a2 + 1/b2, 1/a2 + 1/b2 ]
        """
        return 1/(np.nansum(1/np.array(a), axis=0))

    def invers_array_square_sum(self, a):
        """Calculates the invers sum of columns the given array.
        
        .. code ::
            
            invers_array_sum([
                            [a1, a2, a3],
                            [b1, b2, b3]
                        ]) = 1/sqrt([1/a1^2 +1/b1^2, 1/a2^2 + 1/b2^2, 1/a2^2 + 1/b2^2 ])
        """
        return 1/np.sqrt(np.nansum(1/np.power(np.array(a), 2), axis=0))

    def weight_array_mean(self, x, w):
        """ Calculates  a w weighted array mean following 
        Cox, Metrologia, 2002, 39, 591,  equation (1)
        """
        return np.nansum(np.array(x)/np.power(np.array(w), 2), axis=0)/np.nansum(1/np.power(np.array(w), 2), axis=0)

class Expansion(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Expansion', quant)

class Range(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Range', quant)

class Mass(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Mass', quant)

class Temperature(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Temperature', quant)

class Pressure(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Pressure', quant)

class Flow(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Flow', quant)

class Conductance(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Conductance', quant)

class Drift(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Drift', quant)

class OutGasRate(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'OutGasRate', quant)

class Position(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Position', quant)

class Error(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Error', quant)

class Sigma(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Sigma', quant)

class Uncertainty(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Uncertainty', quant)

class Time(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Time', quant)

    def get_rmt(self, dict_type, unit):
        """Returns the relative measurement.

        :param dict_type: name of the Type (e.g. amt_fill)
        :type dict_type: str
        :param unit: expected unit of the Type (e.g. ms)
        :type unit: str
        :returns: relative measure time
        :rtype: np.array | None
        """
        val = self.get_value(dict_type, unit)

        if val is not None:
            val = val - val[0]

        return val

    def amt_to_date(self,  dict_type, unit):
        """gets and converts an array containing _a_bsolut _m_easure _t_ime
        to a date string.

        :param dict_type: name of the Type (e.g. amt_fill)
        :type dict_type: str
     
        :param unit: expected unit of the Type (e.g. ms)
        :type unit: str
        
        :returns: relative measure time
        :rtype: np.array | None
        """ 
        amt = self.get_value(dict_type, unit)
        if unit == "ms":        
            return np.array([datetime.fromtimestamp(d/1000.0).strftime('%Y-%m-%d %H:%M:%S') for d in amt])
        else:
            sys.exit("todo: care about unit conversion")



class Date(Values):
    def __init__(self, doc, quant="Measurement"):
        super().__init__(doc, 'Date', quant)
    
    def first_measurement(self):
        """Returns the first measurement date. The expected
        structure is:
        
        .. code-block:: javascript
        
             "Date": [
                        {
                        "Type": "measurement",
                        "Value": [ "2018-10-19 09:01", "2018-10-20 09:01"]
                        }
                     ]
        
        at the path: ``Calibration.Measurement``

        :returns: first entry where the type is measurement
        :rtype: str
        """

        date_arr = self.get_str('measurement')
        if isinstance(date_arr, np.ndarray):
            if isinstance(date_arr[0], str):
                date = date_arr[0].split(' ')[0]
                if not len(date) == 10: 
                    sys.exit("implement me!")
            else:
                sys.exit("implement me!")
        else:
            sys.exit("implement me!")

        return date


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
            self.log.warn("No gas entry found in AuxValues try ToDo.Gas")
            return None



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
