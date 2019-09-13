import unittest
import numpy as np
import sympy as sym
from .values import Values, Date


class TestValues(unittest.TestCase):

    def setUp(self):
        pass


    def test_round_to_sig_dig(self):

      v = Values({})

      val = [0, 1.0234e-05, 0.00010234, 0.0010234, 0.010234, 0.10234, 1.0234, 10.234, 102.34, 1023.4, 10234, 102340, 1023400, 10234000]
      res = ['0.00', '0.0000102', '0.000102', '0.00102', '0.0102', '0.102', '1.02', '10.2', '102', '1020', '10200', '102000', '1020000', '10200000']
      res_sci = ['0e-02', '1.02e-05', '1.02e-04', '1.02e-03', '1.02e-02', '1.02e-01', '1.02e+00', '1.02e+01', '1.02e+02', '1.02e+03', '1.02e+04', '1.02e+05', '1.02e+06', '1.02e+07']
      for i in range(len(val)): self.assertEqual(v.round_to_sig_dig(val[i], 3), res[i])
      for i in range(len(val)): self.assertEqual(v.round_to_sig_dig(val[i], 3, scientific=True), res_sci[i])

      val = 4.65367515e-8
      dig = [1, 0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -20]
      res = ['0.00000005', '0.0000000', '0.000000', '0.00000', '0.0000', '0.000', '0.00', '0.0', '0', '0', '0', '0', '0', '0']
      res_sci = ['5e-08', '0e-07', '0e-06', '0e-05', '0e-04', '0e-03', '0e-02', '0e-01', '0e+00', '0e+01', '0e+02', '0e+03', '0e+04', '0e+13']
      for i in range(len(dig)): self.assertEqual(v.round_to_sig_dig(val, dig[i]), res[i])
      for i in range(len(dig)): self.assertEqual(v.round_to_sig_dig(val, dig[i], scientific=True), res_sci[i])

      val = 0
      dig = [20, 10, 5, 2, 1, 0, -1, -2, -5, -10, -20]
      res = ['0.0000000000000000000', '0.000000000', '0.0000', '0.0', '0', '0', '0', '0', '0', '0', '0']
      res_sci = ['0e-19', '0e-09', '0e-04', '0e-01', '0e+00', '0e+01', '0e+02', '0e+03', '0e+06', '0e+11', '0e+21']
      for i in range(len(dig)): self.assertEqual(v.round_to_sig_dig(val, dig[i]), res[i])
      for i in range(len(dig)): self.assertEqual(v.round_to_sig_dig(val, dig[i], scientific=True), res_sci[i])    

    def test_inverse_array_sum(self):
      v = Values({})

      a = np.array([1, 1, 1])
      b = []
      b.append(a)
      b.append(a)
      r = v.invers_array_sum(b)
      
      self.assertEqual(r[0], 0.5)
      self.assertEqual(r[1], 0.5)
      self.assertEqual(r[2], 0.5)

    def test_inverse_array_square_sum(self):
      v = Values({})

      u = np.array([[1, 2, 3],
                    [1, 2, 3]])
      
      r = v.invers_array_square_sum(u)
      
      self.assertAlmostEqual(r[0], (1/(1/1.**2 + 1/1.**2))**0.5)
      self.assertAlmostEqual(r[1], (1/(1/2.**2 + 1/2.**2))**0.5)
      self.assertAlmostEqual(r[2], (1/(1/3.**2 + 1/3.**2))**0.5)

    def test_weight_mean_1(self):
      v = Values({})

      u = np.array([[1, 1, 1],
                    [1, 1, 1]])
      p = np.array([[1, 2, 3],
                    [1, 2, 3]])

      r = v.weight_array_mean(p, u)
           
      self.assertAlmostEqual(r[0], 1)
      self.assertAlmostEqual(r[1], 2)
      self.assertAlmostEqual(r[2], 3)

    def test_weight_mean_2(self):
      v = Values({})

      u = np.array([[0.1, 0.1, 0.1],
                    [0.1, 0.1, 0.1]])
      p = np.array([[1, 2, 3],
                    [1, 2, 3]])

      r = v.weight_array_mean(p, u)
      
      self.assertAlmostEqual(r[0], 1)
      self.assertAlmostEqual(r[1], 2)
      self.assertAlmostEqual(r[2], 3)

    def test_weight_mean_3(self):
      v = Values({})

      u = np.array([[1, 1, 1],
                    [0.1, 0.1, 0.1]])
      p = np.array([[2, 2, 2],
                    [1, 1, 1]])

      r = v.weight_array_mean(p, u)
      
      self.assertAlmostEqual(r[0], 1.01, 3)
      self.assertAlmostEqual(r[1], 1.01, 3)
      self.assertAlmostEqual(r[2], 1.01, 3)