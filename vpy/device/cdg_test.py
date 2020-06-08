import unittest
import numpy as np
import sympy as sym
import copy
from vpy.device.cdg import Cdg


class TestCdg(unittest.TestCase):

    def setUp(self):
        self.cob = {"CalibrationObject": {
                      "Name": "test-CDG",
                      "Setup": {},
                      "Device":{}
                    }
        }
        self.p_cal = np.array([0.01, 0.1, 1, 10, 100, 1000, 1e4, 1e5]).astype(np.float) #Pa
        self.p_ind = np.array([0.0101, 0.101, 1.01, 10.1, 101, 1010, 1.01e4, 1.01e5]).astype(np.float) #Pa
    
    def test_instance_1(self):
        """should cal error
        """

        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'
        cob['CalibrationObject']['Device']['Producer'] = 'MKS Inc.'
        cdg = Cdg({}, cob)
        self.assertEqual(cdg.unit, 'Pa')
        self.assertAlmostEqual(cdg.min_p, 0.133322)

    def test_error_1(self):
        """should cal error for 1Torr MKS CDG
        """
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '1Torr'
        cob['CalibrationObject']['Device']['Producer'] = 'MKS Inc.'
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
        cob['CalibrationObject']['Setup']['UseFrom'] = "1"
        cob['CalibrationObject']['Setup']['UseTo'] = "13.3"
        cob['CalibrationObject']['Setup']['UseUnit'] = "Pa"
        cdg = Cdg({}, cob)

        p = np.array([  1, 1.4, 
                        np.nan,
                        2,2,2,
                        3,4,np.nan,6,7,8,
                        9,9,9, 
                        np.nan ])
        e = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1 ])
        p = cdg.shape_pressure(p)

        p, l = cdg.rm_nan(p)
        e, _ = cdg.rm_nan(e, l)

        i_p, i_e = cdg.cal_interpol(p, e)
       
        self.assertAlmostEqual(i_e[0] , 1)
        
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
    
    def test_fill_border(self):
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['UseFrom'] = "100"
        cob['CalibrationObject']['Setup']['UseTo'] = "1333.0"
        cob['CalibrationObject']['Setup']['UseUnit'] = "Pa"
        cdg = Cdg({}, cob)
        p = np.array([90, 200, 300, 500, 900, 1000, 1290])
        e = np.array([ 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3, 1e-3 ])

        pe, ee = cdg.fill_to_dev_borders(p, e)

        self.assertEqual(pe[0], cdg.min_p*(1 - cdg.range_extend))
        self.assertEqual(pe[-1], cdg.max_p*(1 + cdg.range_extend))
        self.assertEqual(len(pe), len(p) + 2)
        self.assertEqual(len(ee), len(p) + 2)

        
    def test_voltage_conversion_1(self):
        """Test the voltage conversion with range."""
        cob = copy.deepcopy(self.cob)
        cob['CalibrationObject']['Setup']['TypeHead'] = '10Torr'
        cob['CalibrationObject']['Device']['Producer'] = 'MKS Inc.'
        cdg = Cdg({}, cob)
        p_ind = np.array([1.,10.,
                          1.,10.,
                          1.,10.]) # V
        ind_range =  np.array(["X0.01","X0.01",
                               "X0.1" ,"X0.1",
                               "X1"   ,"X1"]) 
        p = cdg.pressure({"Value":p_ind, "Unit":"V"}, {}, {"Value":ind_range}, unit="Pa")
        
        self.assertEqual(p[5], 1333.22) # 10V in X1
        self.assertEqual(p[4], 133.322) # 1V in X1
        self.assertEqual(p[3], 133.322) # 10V in X0.1
        self.assertEqual(p[2], 13.3322) # 1V in X0.1
        self.assertEqual(p[1], 13.3322) # 10V in X0.01
        self.assertEqual(p[0], 1.33322) # 1V in X0.01

    def test_temp_correction_1(self):
        """Test the temperature correction."""
        cob = copy.deepcopy(self.cob)
        cdg = Cdg({}, cob)

        e = 0.01
        e_vis = 0.001
        e_vis_unit = "1"
        p_cal = 10.
        t_head =  45 + 273.15
        t_gas = 23 + 273.15
        t_norm = 20 + 273.15

        e_dict = {"Value":np.array([e]), "Unit":"1"}
        p_cal_dict = {"Value":np.array([p_cal]), "Unit":"Pa"}
        t_head_dict = {"Value":np.array([t_head]), "Unit":"K"}
        t_gas_dict = {"Value":np.array([t_gas]), "Unit":"K"}
        t_norm_dict = {"Value":np.array([t_norm]), "Unit":"K"}


        e_0 = e_vis + (e - e_vis)*((t_head/t_norm)**0.5 -1)/((t_head/t_gas)**0.5 -1)

        e_1 = cdg.temperature_correction(e_dict, p_cal_dict, t_gas_dict, t_head_dict, t_norm_dict, e_vis, e_vis_unit)[0]
        self.assertAlmostEqual(e_0, e_1)
        
        p_cal_dict = {"Value":np.array([200]), "Unit":"Pa"}
        e_2 = cdg.temperature_correction(e_dict, p_cal_dict, t_gas_dict, t_head_dict, t_norm_dict, e_vis, e_vis_unit)[0]
        self.assertAlmostEqual(e_2, e)

        
        e_dict = {"Value":np.array([e, e, e]), "Unit":"1"}
        p_cal_dict = {"Value":np.array([10, 200, 10]), "Unit":"Pa"}
        t_gas_dict = {"Value":np.array([t_gas, t_gas, t_gas]), "Unit":"K"}

        e_3 = cdg.temperature_correction(e_dict, p_cal_dict, t_gas_dict, t_head_dict, t_norm_dict, e_vis, e_vis_unit)
        self.assertAlmostEqual(e_3[0], e_0)
        self.assertAlmostEqual(e_3[1], e)
        self.assertAlmostEqual(e_3[2], e_0)
