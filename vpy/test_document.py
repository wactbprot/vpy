import unittest
from .document import Document

class TestDU(unittest.TestCase):
    def setUp(self):
        doc = {'A': 'a',
               'B': [
                   {'C': 'c', 'D': 'd'},
                   {'E': 'e', 'F': 'f'}
               ],
               'G': {'H': 'c', 'I': 'd'},
               'Meas':[
                {'Type':'a', 'Value':[1,2,3], 'Unit':'s'},
                {'Type':'b', 'Value':['1','2','3'], 'Unit':'s'}
                ]
               }
        self.Doc = Document(doc)

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
        """Shold return a numpy vector
        """
        res = self.Doc.get_value('b', 's')

        self.assertTrue(type(res).__module__ == 'numpy')
        self.assertEqual(res[0], '1')



if __name__ == '__main__':
    unittest.main()
