import unittest
import numpy as np
import sympy as sym
import copy
from vpy.device.cdg import Cdg, InfCdg, Se3Cdg


class TestAnalysis(unittest.TestCase):

    def setUp(self):
        self.cob = {"CalibrationObject": {
                    "Name": "test-CDG",
                      "Setup": {}
                    }
        }
    
    def test_instance_1(self):
        """should cal error
        """

        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'        
        cdg = Se3Cdg({}, cob)
        self.assertEqual(cdg.unit, 'Pa')
        self.assertAlmostEqual(cdg.min_p, 0.13332)

    def test_error_1(self):
        """should cal error
        """
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'
        
        cdg = Se3Cdg({}, cob)
        
        p_cal = np.array([0.9, 1, 10, 100, 1000, 10000]).astype(np.float) #Pa
        p_ind = np.array([0.901, 1.01, 10.1, 101, 1010, 10100]).astype(np.float) #Pa

        err, unit = cdg.error(p_cal, p_ind)
        self.assertEqual(unit, '1')
        print(err) ##