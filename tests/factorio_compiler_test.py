from factorio_microcontroller.factorio_compiler import FactorioCompiler
import unittest


class FactorioCompilerTest(unittest.TestCase):
    def setUp(self):
        self.fc = FactorioCompiler()

    def test_find_scale(self):
        assembly = "f" # todo load test assebmly
        self.fc.compile_to_bin(assembly, 'test.txt')
        self.assertTrue(True)
