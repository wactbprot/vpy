import unittest
from .document import Document

class TestDU(unittest.TestCase):
    def setUp(self):
        doc = {'A': 'a',
               'B': [
                   {'C': 'c', 'D': 'd'},
                   {'E': 'e', 'F': 'f'}
               ],
               'G': {'H': 'c', 'I': 'd'}
               }
        self.Doc = Document(doc)

    def test_get_1(self):
        """flat obj
        """
        res = self.Doc.get_object('A', 'a')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['A'], 'a')

    def test_get_2(self):
        """nested obj level 1
        """
        res = self.Doc.get_object('H', 'c')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['H'], 'c')

    def test_get_3(self):
        """nested obj in list
        """
        res = self.Doc.get_object('C', 'c')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['C'], 'c')

    def test_get_4(self):
        """nested obj in list, type not available
        """
        res = self.Doc.get_object('X', 'c')

        self.assertIsNone(res)

    def test_get_5(self):
        """nested obj in list, value not available
        """
        res = self.Doc.get_object('C', 'i')

        self.assertIsNone(res)

    def test_get_6(self):
        """nested obj in list, self.Doc
        """
        res = self.Doc.get_object('C', 'c')

        self.assertTrue(type(res) is dict)
        self.assertEqual(res['C'], 'c')

if __name__ == '__main__':
    unittest.main()
