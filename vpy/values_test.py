import unittest
import numpy as np
import sympy as sym
from .values import Values, Date


class TestValues(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skip("methode will be removed")
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
        d = date.parse_labview_date()
        self.assertEqual(d[0], "2018-05-28")
        self.assertEqual(d[1], "2018-05-29")
        self.assertEqual(d[2], "2018-05-30")
        self.assertEqual(d[3], "error")
        self.assertEqual(d[4], "error")


    def test_round_to_sig_dig(self):

      v = Values({})

      val = [0, 1.0234e-05, 0.00010234, 0.0010234, 0.010234, 0.10234, 1.0234, 10.234, 102.34, 1023.4, 10234, 102340, 1023400, 10234000]
      res = ['0.0', '1.0e-05', '1.0e-04', '0.0010', '0.010', '0.10', '1.0', '10', '100', '1000', '10000', '1.0e+05', '1.0e+06', '1.0e+07']
      for i in range(len(val)): self.assertEqual(v.round_to_sig_dig(val[i], 2), res[i])

      val = np.pi**50
      dig = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7]
      res = ['0e+27', '0e+26', '1e+25', '7e+24', '7.2e+24', '7.20e+24', '7.203e+24', '7.2027e+24', '7.20267e+24', '7.202672e+24']
      for i in range(len(dig)): self.assertEqual(v.round_to_sig_dig(val, dig[i]), res[i])

      val = 4.65367515e-8
      dig = [1, 0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -20]
      res = ['5e-08', '0e-07', '0e-06', '0e-05', '0.0000', '0.000', '0.00', '0.0', '0', '0e+01', '0e+02', '0e+03', '0e+04', '0e+13']
      for i in range(len(dig)): self.assertEqual(v.round_to_sig_dig(val, dig[i]), res[i])        



