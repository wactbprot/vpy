import sys
import copy
from .pkg_log import Log
import numpy as np
import sympy as sym

class Document(object):

    def __init__(self, doc):
        """Initialisation of Document class.

        :param doc: doc document to search and extract
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
        self.log.debug("working on list {}".format(iter_list))
        for i, val in enumerate(iter_list):
            il_item = "{}{}{}".format(prefix, val, sufix)
            self.log.debug("search for name: {}".format(il_item))
            vec = self.get_value(il_item, unit)

            if i == 0:
                M = len(vec)
                ret = np.full((N, M), np.nan)

            ret[i][:] = vec[:]

        return ret

    def get_obj(self, t, unit):
        """Abbreviation for the method ``get_object``:
        searches an dict (o) by means of method ``get_object``.
        Compares ``o.Unit`` with ``unit`` parameter and returns
        *numpy* typed values by means of method ``get_value``.

        :param val: val value of the key Type to search for
        :type val: str
        :param unit: unit expected unit of the returned result
        :type unit: str

        :returns: dict with Type, Value, Unit keys
        :rtype: {Type: str, Unit: str, Value: np.array}
        """
        ret = None

        obj = self.get_object("Type", t)
        if obj is not None:
            val = self.get_value(t, unit, obj)
            obj["Value"] = val
            ret = obj
        else:
            self.log.warning("Type {} not found".format(t))

        return ret

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
                    errmsg = "Unit is {} not {}".format(obj["Unit"], unit)
                    self.log.error(errmsg)
                    sys.exit(errmsg)

        else:
            self.log.error("Expression of Type {} not found".format(t))

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

        if "Value" in obj:
            if isinstance(obj["Value"], list):
                return np.array(obj["Value"])

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
                errmsg="more than one value"
                self.log.error(errmsg)
                sys.exit(errmsg)
        else:
            errmsg="value is empty"
            self.log.error(errmsg)
            sys.exit(errmsg)
        return ret

    def get_value(self, t, unit, o=False):
        """Gets an dict by means of  ``o=get_object()``,
        compares o.Unit with unit and returns
        numpy typed array.

        :param t: value for type key
        :type t: str

        :param unit: unit of value
        :type unit: str

        :returns: np.array
        :rtype: np.array
        """

        ret = None
        if o:
            obj = o
        else:
            obj = self.get_object("Type", t)

        if obj:
            if "Unit" in  obj:
                if obj["Unit"] == unit:
                    self.log.debug("unit of Type: {} is {}".format(t, unit))
                else:
                    errmsg="Unit is {} not {}".format(obj["Unit"], unit)
                    self.log.error(errmsg)
                    sys.exit(errmsg)

            if "Value" in obj:
                if isinstance(obj["Value"], str):
                    ret = np.asarray([np.float64(obj["Value"])], dtype="f")

                if isinstance(obj["Value"], list):
                    ret = np.asarray(obj["Value"])

                if isinstance(obj["Value"], float):
                    ret = np.array([obj["Value"]])

                if isinstance(obj["Value"], int):
                    ret = np.array([obj["Value"]])

        else:
            self.log.warning("Value of Type {} not found".format(t))
        return ret

    def get_object(self, key, val, o=False, d=0):
        """Recursive  searches obj for
        ''obj[key] == val'' and returns obj

        :param key: key to search for
        :type key: str

        :param val: val of key
        :type val: str

        :returns: res
        :rtype: dict
        """
        # self.log.debug("recursion level is: {}".format(d))
        if o:
            obj = copy.deepcopy(o)
        else:
            obj = copy.deepcopy(self.doc)

        if isinstance(obj, dict):
            if key in obj and obj[key] == val:
                return obj
            else:
                for k, v in obj.items():
                    if isinstance(v, dict) or isinstance(v, list):
                        res = self.get_object(key, val, v, d + 1)
                        if res is not None:
                            return res

        if isinstance(obj, list):
            for l in obj:
                if isinstance(l, dict) or isinstance(l, list):
                    res = self.get_object(key, val, l, d + 1)
                    if res is not None:
                        return res
