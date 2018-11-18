import unittest
import numpy as np
import sympy as sym
from .analysis import Analysis


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.Ana = Analysis({})

    def test_store_pick_1(self):
        """store int, pick array containing float
        """
        self.Ana.store(quant="A", type="b", value=1, unit= "u", sd = 0.1, n = 10)
        v = self.Ana.pick("A", "b", "u")
        self.assertEqual(v[0], 1.)

    def test_store_pick_2(self):
        """store array, pick array containing float
        """
        self.Ana.store("A", "b", [1], "u")
        v = self.Ana.pick("A", "b", "u")
        self.assertEqual(v[0], 1.)

    def test_store_dict_1(self):
        """store dict introduce array
        """
        d = {"b": [1], "u":"m"}
        self.Ana.store_dict("D", d)
        ana = self.Ana.get_all()
        self.assertEqual(ana["Values"]["D"], [d])

    def test_store_dict_2(self):
        """store dict plain
        """
        d = {"b": [1], "u":"m"}
        self.Ana.store_dict("D", d, plain=True)
        ana = self.Ana.get_all()
        self.assertEqual(ana["Values"]["D"], d)

    def test_store_dict_3(self):
        """store dict plain w/o destination
        """
        d = {"b": [1], "u":"m"}
        self.Ana.store_dict("E", d, dest=None, plain=True)
        ana = self.Ana.get_all()
        self.assertEqual(ana["E"], d)

    def test_store_pick_4(self):
        """store int, pick array containing float with stats
        """
        self.Ana.store(quant="A", type="b", value=1, unit= "u", sd = 0.1, n = 10)
        v, sd, n = self.Ana.pick("A", "b", "u", with_stats=True)
        self.assertEqual(v[0], 1.)
        self.assertEqual(sd[0], .1)
        self.assertEqual(n[0], 10.)

    def test_store_auxvalues_1(self):
        """should store list in AuxValues
        """
        aux = {
            "A": [1,2,3,4],
            "B": [5,6,7,8]
            }

        self.Ana.store_dict(quant=None, d=aux, dest="AuxValues", plain=True)
        
        doc = self.Ana.build_doc()
        self.assertTrue('Analysis' in doc)
        self.assertTrue('AuxValues' in doc['Analysis'])
        self.assertTrue('A' in  doc['Analysis']['AuxValues'])
        self.assertTrue('B' in  doc['Analysis']['AuxValues'])
        self.assertTrue(isinstance( doc['Analysis']['AuxValues']['A'], list))
        
    def test_pick_auxvalues_1(self):
        """should store list in AuxValues
        """
        aux = {
            "A": [1,2,3,4],
            "B": [5,6,7,8]
            }
        self.Ana.store_dict(quant=None, d=aux, dest="AuxValues", plain=True)
        d = self.Ana.pick_dict(quant='A', dict_type=None, dest="AuxValues")
        self.assertEqual(d[0], 1)