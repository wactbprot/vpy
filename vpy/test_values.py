import unittest
import numpy as np
import sympy as sym
from .values import Date


class TestToDo(unittest.TestCase):

    def setUp(self):
        pass

    def test_date_labview(self):
        """
        """
        doc = {"Calibration":{"Measurement":{"Values":{"Date": {
          "Type": "Date",
          "Value": [
            "Mo, Mai 28, 2018",
            "Di, Mai 29, 2018",
            "Mi, Mai 30, 2018",
            " Mai 30, 2018",
            "Mi, Mai 30",
          ]}}}}}
        date = Date(doc)
        d = date.parse_labview_date("Date")
        self.assertEqual(d[0], 1527458400.0)
        self.assertEqual(d[1], 1527544800.0)
        self.assertEqual(d[2], 1527631200.0)
        self.assertTrue(np.isnan(d[3]))
        self.assertTrue(np.isnan(d[4]))