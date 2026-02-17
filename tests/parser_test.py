import random
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, "../factorio_microcontroller/go_compiler")

from lexer import Token, Lexer
from parser import Parser, OperationNode

TEST_RESOURCE_FOLDER = Path(__file__).parent.parent / "tests/resources"


@dataclass
class UnravelCase:
    tokens: [Token]
    expected: int


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.lexer = Lexer()
        self.parser = Parser()

    def reduce_node(self, node: OperationNode):
        if not node.operand1 or not node.operand2:
            print("???")
        if type(node.operand1) is OperationNode:
            l = self.reduce_node(node.operand1)
        else:
            l = int(node.operand1.value)
        if type(node.operand2) is OperationNode:
            r = self.reduce_node(node.operand2)
        else:
            r = int(node.operand2.value)

        match node.operator:
            case "+":
                return l + r
            case "-":
                return l - r
            case "*":
                return l * r
            case "/":
                return l / r

    def test_unravel(self):
        cases = [
            "6-5*2*2\n",
            "2*3+4+5\n",
            "6-5*2*2+4+7/8-8*8/8-9/3/1-9+1+2+4+6-7-1-1-6+1*8-1+8\n",
            "102+12+3+2+1-2\n",
            "6/3+8/8*3\n",
            "5-4+8*8-6\n",
            "2*3+4*7*2\n",
            "3+4*2+3\n",
            "3+4*2+3*4\n",
            "3*4+2\n",
            "3+4*2\n",
            "102+12\n",
            "3-2*3-3*8\n",
            "1-2*3+4*7*2\n",
        ]

        for c in cases:
            self.unravel_case(c)

    def test_unravel_fuzzy(self):
        count = 100
        operators = ["+", "-", "*", "/"]
        for c in range(count):
            op = ""
            for i in range(random.randint(10, 30)):
                op += str(random.randint(1, 9))
                op += operators[random.randint(0, len(operators) - 1)]

            op = op[:-1] + "\n"
            self.unravel_case(op)

    def unravel_case(self, case):
        tokens = self.lexer.tokenize_str(case)
        root_node = self.parser.unravel(tokens, 0)
        result = self.reduce_node(root_node)

        expected = eval(case)
        self.assertEqual(expected, result, case)


if __name__ == '__main__':
    unittest.main()
