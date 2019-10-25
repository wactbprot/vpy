import unittest
import numpy as np
from vpy.analysis import Analysis
from vpy.standard.se3.uncert import Uncert as UncertSe3

class TestUncertSE3(unittest.TestCase):

    def setUp(self):
        self.ana = Analysis({})
        self.uncert = UncertSe3({})
    
    def test_cmc(self):
        """tests the piecewise repeatability 
        """

        self.ana.store("Pressure", "cal", [0.026, 0.027, 0.028, 0.3, 0.4,  0.72, 0.74, 9., 10., 999., 1001., 8000.,  8001.], "Pa" )
        self.uncert.cmc(self.ana)
        u = self.ana.pick("Uncertainty",  "standard", "1" )
        print(u)
        self.assertEqual(u[0],  0.0014 )  
        self.assertEqual(u[1],  0.0014 )  
        self.assertEqual(u[2],  0.001  )  
        self.assertEqual(u[3],  0.001  )  
        self.assertEqual(u[4],  0.00092)  
        self.assertEqual(u[5],  0.00092)  
        self.assertEqual(u[6],  0.00086)  
        self.assertEqual(u[7],  0.00086)
        self.assertEqual(u[8],  0.00075)  
        self.assertEqual(u[9],  0.00075)  
        self.assertEqual(u[11],  0.00019)  
        self.assertEqual(u[12],  0.00014)  
