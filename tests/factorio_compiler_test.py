from factorio_microcontroller.factorio_compiler import FactorioCompiler
import unittest
import filecmp
import os


class FactorioCompilerTest(unittest.TestCase):
    def setUp(self):
        self.fc = FactorioCompiler()

    def test_compile_to_bin(self):
        assembly_file = "./resources/test_assembly.txt"
        actual_assembly_file = "./resources/test_bin_actual.txt"
        self.fc.compile_to_bin(assembly_file, actual_assembly_file)
        self.assertTrue(filecmp.cmp("./resources/test_bin_expected.txt", "./resources/test_bin_actual.txt"))

        os.remove(actual_assembly_file)


if __name__ == '__main__':
    unittest.main()
