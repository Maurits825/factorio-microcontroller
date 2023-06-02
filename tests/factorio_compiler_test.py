from factorio_microcontroller.factorio_compiler import FactorioCompiler
import unittest
import filecmp
import os
from pathlib import Path

TEST_RESOURCE_FOLDER = Path(__file__).parent.parent / "tests/resources"


class FactorioCompilerTest(unittest.TestCase):
    def setUp(self):
        self.fc = FactorioCompiler()

    # TODO could split test assembly bins into folders for each opcode ops like memory, i/o, alu...
    def test_compile_to_bin(self):
        assembly_file = TEST_RESOURCE_FOLDER / "test_assembly.txt"
        binary_file = self.fc.compile_to_bin(str(assembly_file))
        expected_binary_file = TEST_RESOURCE_FOLDER / "test_bin_expected.bin"

        self.assertTrue(filecmp.cmp(expected_binary_file, binary_file))

        os.remove(binary_file)


if __name__ == '__main__':
    unittest.main()
