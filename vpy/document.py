import sys
import copy
from .pkg_log import Log
import numpy as np
import sympy as sym

class Document(object):

    def __init__(self, doc):
        """Initialisation of Document class.

        :param doc: doc document to search and extract from
        :type doc: dict
        """
        self.doc = copy.deepcopy(doc)
        self.log = Log().logger(__name__)

    def get_all(self):
        """Returns the entire document

        :returns: doc
        :rtype: dict
        """
        return self.doc


    def get_array(self, prefix, iter_list, sufix, unit):
        """Generates a np.array  of values with analog type strings
        like ``ch_1001_before`` ... ``ch_1030_before``.

        In this example ``ch_`` would be the ``prefix``,
        ``[1001, ..., 1030]`` is the ``iter_list`` and
        ``_before`` is the sufix.

        .. note::
            * types are in rows
            * measurement points are in columns

        :param prefix: prefix of the type
        :type doc: str
        :param iter_list: list to iterate over
        :type iter_list: list

        :param sufix: sufix of the type
        :type sufix: str

        :returns: array of arrays
        :rtype: np.array
        """

        N = len(iter_list)
        for i, val in enumerate(iter_list):
            il_item = "{}{}{}".format(prefix, val, sufix)
            vec = self.get_value(il_item, unit)

            if i == 0:
                M = len(vec)
                ret = np.full((N, M), np.nan)

            ret[i][:] = vec[:]

        return ret

    def get_value_and_unit(self, d_type):
        """Intended use for this method: **extracting values when unit is unknown**.
        Searches ``dict`` by means of method ``get_object()`` and extracts the unit.
        Uses ``get_value()`` to shape values.

        :param type: val value of the key Type to search for
        :type type: str

        :returns: values, unit
        :rtype: np.array, str
        """
        value = None
        unit = None

        obj = self.get_object("Type", d_type)
        if obj is not None:
            if "Unit" in obj:
                unit = obj['Unit']
                value = self.get_value(d_type, unit, obj)

        return value, unit



    def get_expression(self, t, unit, o=False):
        """Gets an dict by means of ``o=get_object()``,
        compares ``o.Unit`` with unit and returns
        sym.sympyfied expression.

        :param t: value for type key
        :type t: str

        :param unit: unit of value
        :type unit: str

        :returns: expression
        :rtype: sym.sympyfied
        """
        ret = None
        if o:
            obj = o
        else:
            obj = self.get_object("Type", t)

        if obj:
            if "Unit" in  obj:
                if obj["Unit"] == unit:
                    if "Expression" in obj:
                        ret = sym.sympify(obj["Expression"])

                    if "Value" in obj:
                        ret = sym.sympify(obj["Value"])
                else:

                    sys.exit("Unit is {} not {}".format(obj["Unit"], unit))

        return ret

    def get_str(self, t):
        """Gets an dict by means of ``o=get_object()``,
        returns numpy typed array.

        :param t: value for type key
        :type t: str

        :returns: np.array
        :rtype: np.array
        """

        obj = self.get_object("Type", t)

        if obj and "Value" in obj:
            if isinstance(obj["Value"], list):
                return np.array(obj["Value"])
        else:
            return None

    def get_value_full(self, t, unit, N):
        """same as ``self.get_value`` but returns
        an array of the length ``self.no_of_meas_points``

        :param t: value for type key
        :type t: str

        :param unit: unit of value
        :type unit: str

        :param N: number of values to return
        :type N: int

        :returns: np.array
        :rtype: np.array
        """
        ret = None
        val = self.get_value(t, unit)
        if val is not None:
            if np.shape(val) == (1,):
                ret = np.full(N, val)
            else:
                sys.exit("more than one value")
        else:
            sys.exit("value is empty")

        return ret

    def get_value(self, value_type, value_unit, o=False, with_stats=False):
        """Gets an dict by means of  ``o=get_object()``,
        compares o.Unit with value_unit and returns
        numpy typed array.

        :param value_type: value for type key
        :type value_type: str

        :param value_unit: value_unit of value
        :type value_unit: str

        :returns: np.array
        :rtype: np.array
        """

        value_ret = None
        if o:
            obj = o
        else:
            obj = self.get_object("Type", value_type)

        if obj:
            if "Unit" in  obj:
                if obj["Unit"] != value_unit:
                    sys.exit("On attempt to get value of Type {}: Unit is {} not {}".format(value_type, obj["Unit"], value_unit))

            if "Value" in obj:
                value_ret = self.safe_float_array(obj['Value'])
            else:
                value_ret = None
            if "SdValue" in obj:
                sd_ret = self.safe_float_array(obj['SdValue'])
            else:
                sd_ret = None

            if "N" in obj:
                n_ret = self.safe_float_array(obj['N'])
            else:
                n_ret = None

        if with_stats:
            return value_ret, sd_ret, n_ret
        else:
            return value_ret

    def safe_float_array(self, value):
        """Ensures the return value to be a numpy array of float

        :param value: value
        :type value: str|list|float|int

        :returns: ret
        :rtype: np: array of type np.float
        """
        if isinstance(value, str):
            ret = np.asarray([value], dtype=np.float)
        if isinstance(value, list):
            ret = np.asarray(value, dtype=np.float)
        if isinstance(value, float):
            ret = np.array([value], dtype=np.float)
        if isinstance(value, int):
            ret = np.array([value], dtype=np.float)

        return ret

    def get_dict(self, key, value, o=False):
        """ Wrapper methode for get_object with more healthy name.

        :param key: key to search for
        :type key: str

        :param val: val of key
        :type val: str

        :returns: res
        :rtype: dict
        """
        return self.get_object(key, value, o=False)

    def get_object(self, key, value, o=False):
        """Recursive  searches obj for
        ''obj[key] == val'' and returns obj

        :param key: key to search for
        :type key: str

        :param val: val of key
        :type val: str

        :returns: res
        :rtype: dict
        """

        if o:
            obj = copy.deepcopy(o)
        else:
            obj = copy.deepcopy(self.doc)

        if isinstance(obj, dict):
            if key in obj and obj[key] == value:
                return obj
            else:
                for k, v in obj.items():
                    if isinstance(v, dict) or isinstance(v, list):
                        res = self.get_object(key, value, v)
                        if res is not None:
                            return res

        if isinstance(obj, list):
            for l in obj:
                if isinstance(l, dict) or isinstance(l, list):
                    res = self.get_object(key, value, l)
                    if res is not None:
                        return res
