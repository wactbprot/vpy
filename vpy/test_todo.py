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
        """
        """
        pcal = np.array([0.01, 0.0109, 0.0099])
        self.ToDo.make_average_index(pcal, "mbar")
        self.assertEqual(len(self.ToDo.average_index), 16)
        self.assertEqual(len(self.ToDo.average_index[0]), 3)
        self.assertEqual(len(self.ToDo.average_index[1]), 0)
