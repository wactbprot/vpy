import unittest
import numpy as np
import sympy as sym
import copy
from vpy.device.cdg import Cdg


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.cob = {"CalibrationObject": {
                    "Name": "test-CDG",
                      "Setup": {}
                    }
        }
        self.p_cal = np.array([0.01, 0.1, 1, 10, 100, 1000, 1e4, 1e5]).astype(np.float) #Pa
        self.p_ind = np.array([0.0101, 0.101, 1.01, 10.1, 101, 1010, 1.01e4, 1.01e5]).astype(np.float) #Pa
    
    def test_instance_1(self):
        """should cal error
        """

        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'        
        cdg = Cdg({}, cob)
        self.assertEqual(cdg.unit, 'Pa')
        self.assertAlmostEqual(cdg.min_p, 0.13332)

    def test_error_1(self):
        """should cal error for 1Torr CDG
        """
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'
        cdg = Cdg({}, cob)

        err, unit = cdg.error(self.p_cal, self.p_ind, 'Pa')
        self.assertEqual(unit, '1')
        self.assertTrue(np.isnan(err[0]))
        self.assertTrue(np.isnan(err[1]))
        self.assertTrue(np.isnan(err[5]))
        self.assertTrue(np.isnan(err[6]))
        self.assertTrue(np.isnan(err[7]))

        self.assertAlmostEqual(err[2], 1e-2)        
        self.assertAlmostEqual(err[3], 1e-2)        
        self.assertAlmostEqual(err[4], 1e-2)        

    def test_error_2(self):
        """should cal error for 1000Torr CDG
        """
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1000Torr'
        cdg = Cdg({}, cob)

        err, unit = cdg.error(self.p_cal, self.p_ind, 'Pa')

        self.assertEqual(unit, '1')
        self.assertTrue(np.isnan(err[0]))
        self.assertTrue(np.isnan(err[1]))
        self.assertTrue(np.isnan(err[2]))
        self.assertTrue(np.isnan(err[3]))
        self.assertTrue(np.isnan(err[4]))

        self.assertAlmostEqual(err[5], 1e-2)        
        self.assertAlmostEqual(err[6], 1e-2)        
        self.assertAlmostEqual(err[7], 1e-2)        

    def test_nice_values(self):
        cob = copy.deepcopy(self.cob)
        cdg = Cdg({}, cob)
        vec = cdg.get_nice_vals(1,1000)
       
        self.assertAlmostEqual(len(vec), 30)
        self.assertAlmostEqual(vec[0], 1)
        self.assertAlmostEqual(vec[-1], 1000)
    
    def test_interpol_values(self):
        cob = copy.deepcopy(self.cob)
        cdg = Cdg({}, cob)
        p = np.array([1,2,3,4,5,6,7,8,9,10 ])
        e = np.array([1,1,1,1,1,1,1,1,1,1 ])
        u = np.array([1,1,1,1,1,1,1,1,1,1 ])

        vec = cdg.get_error_interpol(p, e, u)
        print(vec)