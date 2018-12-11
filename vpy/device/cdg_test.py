import unittest
import numpy as np
import sympy as sym
import copy
from vpy.device.cdg import Cdg


class TestCdg(unittest.TestCase):

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

        p_cal = cdg.shape_pressure(self.p_cal)
        p_cal, l = cdg.rm_nan(p_cal)
        p_ind, _ = cdg.rm_nan(self.p_ind, l)

        err, unit = cdg.error(p_cal, p_ind, 'Pa')
        self.assertEqual(unit, '1')

        self.assertAlmostEqual(err[0], 1e-2)        
        self.assertAlmostEqual(err[1], 1e-2)        
        self.assertAlmostEqual(err[2], 1e-2)        

    def test_nice_values(self):
        cob = copy.deepcopy(self.cob)
        cdg = Cdg({}, cob)
        vec = cdg.get_default_values(1,1000)
       
        self.assertAlmostEqual(vec[0], 1)
        self.assertAlmostEqual(vec[-1], 1000)
    
    def test_interpol_values(self):
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'
        cdg = Cdg({}, cob)

        p = np.array([  1, 1.4, 
                        np.nan,
                        2,2,2,
                        3,4,np.nan,6,7,8,
                        9,9,9, 
                        np.nan ])
        e = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ])
        u = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ])
        p = cdg.shape_pressure(p)

        p, l = cdg.rm_nan(p)
        e, _ = cdg.rm_nan(e, l)
        u, _ = cdg.rm_nan(u, l)

        i_p, i_e, i_u = cdg.cal_interpol(p, e, u)

        self.assertAlmostEqual(i_p[0] , (1+1.4+2)/3)
        self.assertAlmostEqual(i_e[0] , 1)
        self.assertAlmostEqual(i_u[0] , 1)
        
    def test_rm_nan_1(self):
        """
        a = [1,2,3,]
        np.shape(a) -->       (3,)
        a = np.array([1,2,3,])
        np.shape(a) -->       (3,)
        """
        cob = copy.deepcopy(self.cob)
        cdg = Cdg({}, cob)
        val, ldx = cdg.rm_nan(np.array([np.nan,np.nan]))
        self.assertEqual( np.shape(val)[0], 0)
        self.assertEqual( np.shape(ldx)[0], 2)
        