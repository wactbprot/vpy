import unittest

from vpy.document_test import TestDocument
from vpy.analysis_test import TestAnalysis
from vpy.values_test import TestValues
from vpy.todo_test import TestToDo
from vpy.device.cdg_test import TestCdg

loader = unittest.TestLoader()
suite  = unittest.TestSuite()

suite.addTests(loader.loadTestsFromTestCase(TestCdg))
suite.addTests(loader.loadTestsFromTestCase(TestToDo))
suite.addTests(loader.loadTestsFromTestCase(TestValues))
suite.addTests(loader.loadTestsFromTestCase(TestAnalysis))
suite.addTests(loader.loadTestsFromTestCase(TestDocument))

runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)