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
