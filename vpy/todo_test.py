import unittest
import numpy as np
import sympy as sym
from .todo import ToDo


class TestToDo(unittest.TestCase):

    def setUp(self):
        doc = {
            "Name": "CDG 10mbar",
            "Standard": "SE2",
            "Type": "error",
            "Gas": "N2",
            "Cmc": True,
            "Repeat": "1",
            "Comment": "ToDo doc für 10mbar CDG Fehler an SE2",
            "Values": {
                "Temperature": {
                    "Type": "target",
                    "Unit": "C",
                    "Value": [
                        "23.0"
                    ]
                },
                "Pressure": {
                    "Type": "target",
                    "Unit": "mbar",
                    "Value": [
                        "0.01",
                        "0.02",
                        "0.03",
                        "0.05",
                        "0.07",
                        "0.1",
                        "0.2",
                        "0.3",
                        "0.5",
                        "0.7",
                        "1",
                        "2",
                        "3",
                        "5",
                        "7",
                        "10"
                    ]
                }
            },
            "Table": {
                "Pressure": [
                    {
                        "Type": "cal",
                        "Unit": "mbar"
                    },
                    {
                        "Type": "ind",
                        "Unit": "mbar"
                    },
                    {
                        "Type": "offset",
                        "Unit": "mbar"
                    }
                ],
                "Error": [
                    {
                        "Type": "relative",
                        "Unit": "1"
                    }
                ],
                "Uncertainty": [
                    {
                        "Type": "total",
                        "Unit": "1"
                    }
                ]
            }
        }
        self.ToDo = ToDo(doc)

    def test_average_index_1(self):
        """Should assign p, p +/-4% to target 
        point p but not p+/-5%.
        """
       
        p_target = self.ToDo.Pres.get_value("target", self.ToDo.pressure_unit)
        N = len(p_target)
        pcal = np.array([p_target[0], # 0.01
                         p_target[0]*(1-0.04), # -4% 
                         p_target[0]*(1+0.04), # +4% 
                         p_target[0]*(1-0.05), # -5% 
                         p_target[0]*(1+0.05), # +5%
                         p_target[-1], # 10
                         p_target[-1]*(1-0.04), # -4% 
                         p_target[-1]*(1+0.04), # +4% 
                         p_target[-1]*(1-0.05), # -5% 
                         p_target[-1]*(1+0.05), # +5% 
        ])

        average_index = self.ToDo.make_average_index(pcal, "mbar")
        
        self.assertEqual(len(average_index), N)
        self.assertEqual(len(average_index[0]), 3)
        self.assertEqual(len(average_index[1]), 0)
        self.assertEqual(len(average_index[-1]), 3)
