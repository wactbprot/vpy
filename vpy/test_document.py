import unittest
import numpy as np
import sympy as sym
from .document import Document

class TestDocument(unittest.TestCase):
    """

    Method Checks
    ==============

    * assertEqual(a, b)	a == b
    * assertNotEqual(a, b)	a != b
    * assertTrue(x)	bool(x) is True
    * assertFalse(x)	bool(x) is False
    * assertIs(a, b)	a is b
    * assertIsNot(a, b)	a is not b
    * assertIsNone(x)	x is None
    * assertIsNotNone(x)	x is not None
    * assertIn(a, b)	a in b
    * assertNotIn(a, b)	a not in b
    * assertIsInstance(a, b)	isinstance(a, b)
    * assertNotIsInstance(a, b)	not isinstance(a, b)

    """
    def setUp(self):
        doc = {'A': 'a',
               'B': [
                   {'C': 'c', 'D': 'd'},
                   {'E': 'e', 'F': 'f'}
               ],
               'G': {'H': 'c', 'I': 'd'},
               'Meas':[
                {'Type':'a', 'Value':[1, 2, 3], 'Unit':'s'},
                {'Type':'b', 'Value':['1', '2', '3'], 'Unit':'s'},
                {'Type':'b_1', 'Value':['1', '2', '3'], 'Unit':'s'},
                {'Type':'b_2', 'Value':['1', '2', '3'], 'Unit':'s'},
                {'Type':'b_3', 'Value':['1', '2', '3'], 'Unit':'s'},
                {'Type':'expr', 'Expression':'2*b', 'Unit':'s'}

                ]
               }
        self.Doc = Document(doc)

    def test_log(self):
        """Should provide log functionality
        """
        self.assertTrue("log" in dir(self.Doc))

    def test_get_object_1(self):
        """flat obj
        """
        res = self.Doc.get_object('A', 'a')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['A'], 'a')

    def test_get_object_2(self):
        """nested obj level 1
        """
        res = self.Doc.get_object('H', 'c')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['H'], 'c')

    def test_get_object_3(self):
        """nested obj in list
        """
        res = self.Doc.get_object('C', 'c')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['C'], 'c')

    def test_get_object_4(self):
        """nested obj in list, type not available
        """
        res = self.Doc.get_object('X', 'c')

        self.assertIsNone(res)

    def test_get_object_5(self):
        """nested obj in list, value not available
        """
        res = self.Doc.get_object('C', 'i')

        self.assertIsNone(res)

    def test_get_object_6(self):
        """nested obj in list
        """
        res = self.Doc.get_object('C', 'c')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['C'], 'c')

    def test_get_value_1(self):
        """Shold return a numpy vector
        """
        res = self.Doc.get_value('a', 's')

        self.assertTrue(type(res).__module__ == 'numpy')
        self.assertEqual(res[0], 1)

    def test_get_value_2(self):
        """Shold return a numpy vector of numbers
        """
        res = self.Doc.get_value('b', 's')

        self.assertTrue(type(res).__module__ == 'numpy')
        self.assertEqual(res[0], 1.0)

    def test_get_str_1(self):
        """Shold return a numpy vector of strings
        """
        res = self.Doc.get_str('b')
        self.assertTrue(type(res).__module__ == 'numpy')
        self.assertEqual(res[0], '1')

    def test_get_all_1(self):
        """Should return the complete Document.
        """
        res = self.Doc.get_all()
        self.assertEqual(res['A'], 'a')

    def test_get_array_1(self):
        """Should return the complete Document.
        """
        res = self.Doc.get_array("b_", (1,2,3), "", "s")
        self.assertEqual(np.shape(res), (3, 3))


    def test_get_expression_1(self):
        """Should return a sympy Expression
        """
        res = self.Doc.get_expression("expr","s")
        self.assertTrue(type(res).__module__ == 'sympy.core.mul')

    def test_get_value_and_unit_1(self):
        """Should return value and unit
        """
        val, unit = self.Doc.get_value_and_unit("a")
        self.assertTrue(len(val) == 3)
        self.assertTrue(unit == "s")
