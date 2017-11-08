import numpy as np
import sys
import copy
from .vpy_io import Io

class Document(object):


    io = Io()
    log = io.log(__name__)
    log.info("start logging")


    def __init__(self, doc):
        """Initialisation of Document class.

        :param doc: doc document to search and extract
        :type doc: dict
        """
        self.doc = doc

    def get_all(self):
        """Returns the entire document

        :returns: doc
        :rtype: dict
        """
        return self.doc

    def test(self):
        """Returns the test string 'ok'

        :returns: ok
        :rtype: string
        """
        return "ok"

    def get_array(self, prefix, iter_list, sufix, unit):
        """Generates a np.array  of values with analog type strings
        like ``ch_1001_before`` ... ``ch_1030_before``.

        In this example ``ch_`` would be the ``prefix``,
        ``[1001, ..., 1030]`` is the ``iter_list`` and
        ``_before`` is the sufix.

        .. note:: Different Types are in different rows. Different
                  measurement points are in different columns.

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
        for i in range(N):
            il_item = "{}{}{}".format(prefix, iter_list[i], sufix)
            self.log.info("search for name: {}".format(il_item))
            vec = self.get_value(il_item, unit)

            if i == 0:
                M = len(vec)
                ret = np.full((N, M), np.nan)

            ret[i][:] = vec[:]

        return ret

    def get_obj(self, val, unit):
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
        obj = self.get_object("Type", val)
        if obj is not None:
            val = self.get_value(val, unit, obj)
            obj['Value'] = val
        else:
            self.log.error("Type " + val + "not found")
            obj = None

        return obj

    def get_value(self, val, unit, o=False):
        """gets Object by means of get_object,
        compares o.Unit with unit and returns
        numpy typed values.
        """
        if o:
            obj = o
        else:
            obj = self.get_object("Type", val)

        ret = None
        if obj:
            if 'Value' in obj and 'Unit' in obj:
                if obj["Unit"] == unit:
                    if isinstance(obj['Value'], str):
                        ret = np.float64(obj['Value'])

                    if isinstance(obj['Value'], list):
                        ret = np.array(obj['Value'], dtype="f")

                    if isinstance(obj['Value'], float):
                        ret = np.array([obj['Value']], dtype="f")

                    if isinstance(obj['Value'], int):
                        ret = np.array([obj['Value']], dtype="f")
                else:
                    ret = "Unit is " + obj["Unit"] + " not " + unit
        else:
            self.log.error("not found")
            ret = "not found"
        return ret

    def get_object(self, key, val, o=False, d=0):
        """Recursive  searches obj for
        '''obj[key] == val''' and returns obj
        """
        self.log.debug("recursion level is: {}".format(d))
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
