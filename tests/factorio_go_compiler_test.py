import filecmp
import os
import unittest
from pathlib import Path

from go_compiler.lexer import Lexer
from go_compiler.parser import Parser

TEST_RESOURCE_FOLDER = Path(__file__).parent.parent / "tests/resources/go_compiler"


class FactorioGoCompilerTest(unittest.TestCase):
    def setUp(self):
        self.lexer = Lexer()
        self.parser = Parser()

    # TODO scuffed, we need a proper in out API
    def test_go_compiler(self):
        src = TEST_RESOURCE_FOLDER / "src1.txt"
        expected_asm = TEST_RESOURCE_FOLDER / "asm1.txt"

        tokens = self.lexer.run(str(src))
        assembly_lines = self.parser.run(tokens)
        asm = "assembly.txt"
        with open(asm, "w", encoding="utf-8") as f:
            f.write("\n".join(assembly_lines))

        self.assertTrue(filecmp.cmp(expected_asm, asm))

        os.remove(asm)


if __name__ == '__main__':
    unittest.main()
