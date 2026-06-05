from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    INT_LITERAL = 0
    OPERATOR = 1
    UNARY_OPERATOR = 2
    SCOPE = 3


@dataclass
class Token:
    type: TokenType
    value: str


@dataclass
class Node:
    operator: Token
    operand1: Token | Node
    operand2: Token | Node | None


precedence = {
    None: 0,
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "**": 3,
}


class AST:
    def __init__(self):
        pass

    def lexer(self, s):
        tokens = []
        i = 0
        while i < len(s):
            c = s[i]
            if c.isdigit():
                value = ""
                while c.isdigit():
                    value += c
                    i += 1
                    if i >= len(s):
                        break
                    c = s[i]
                tokens.append(Token(TokenType.INT_LITERAL, value))
            elif c in ["+", "-", "*", "/"]:
                is_unary = True
                if i > 0 and s[i - 1].isdigit():
                    is_unary = False
                if s[i] == "-" and is_unary:
                    tokens.append(Token(TokenType.UNARY_OPERATOR, c))
                elif s[i + 1] == "*":
                    tokens.append(Token(TokenType.OPERATOR, "**"))
                    i += 1
                else:
                    tokens.append(Token(TokenType.OPERATOR, c))
                i += 1

            elif c in ["(", ")"]:
                tokens.append(Token(TokenType.SCOPE, c))
                i += 1
            else:
                i += 1
        return tokens

    def create_node(self, operands, operators):
        op = operators.pop()
        op2 = operands.pop()
        op1 = None
        if op.type == TokenType.OPERATOR:
            op1 = operands.pop()
        operands.append(Node(op, op1, op2))

    def create_ast(self, tokens: list[Token]):
        operators = [Token(TokenType.OPERATOR, None)]
        operands = []

        i = 0
        while i < len(tokens):
            t = tokens[i]
            match t.type:
                case TokenType.INT_LITERAL:
                    operands.append(t)
                case TokenType.UNARY_OPERATOR:
                    operators.append(t)  # TODO this right?
                case TokenType.OPERATOR:
                    if precedence[t.value] > precedence[operators[-1].value]:
                        operators.append(t)
                    else:
                        while precedence[t.value] <= precedence[operators[-1].value]:
                            self.create_node(operands, operators)
                        operators.append(t)
                case TokenType.SCOPE:
                    if t.value == "(":
                        operators.append(Token(TokenType.OPERATOR, None))
                    else:
                        while operators[-1].value is not None:
                            self.create_node(operands, operators)
                        operators.pop()
            i += 1

        while len(operators) > 0:
            if operators[-1].value is None:
                operators.pop()
                continue
            self.create_node(operands, operators)

        return operands[0]

    def parse_node(self, node: Node):
        if isinstance(node.operand1, Node):
            op1 = self.parse_node(node.operand1)
        else:
            op1 = int(node.operand1.value) if node.operand1 else 0

        if isinstance(node.operand2, Node):
            op2 = self.parse_node(node.operand2)
        else:
            op2 = int(node.operand2.value)

        match node.operator.value:
            case "+":
                return op1 + op2
            case "-":
                return op1 - op2
            case "*":
                return op1 * op2
            case "/":
                return op1 / op2
            case "**":
                return op1 ** op2

    @staticmethod
    def parse(exp):
        a = AST()
        tokens = a.lexer(exp)
        root = a.create_ast(tokens)
        result = a.parse_node(root)
        return result

    def run(self):
        s = "4-(-4*3)"

        tokens = self.lexer(s)
        print("Tokens")
        for t in tokens:
            print(t)

        expected = eval(s)

        # r1 = calc(s, ShuntingYardEvaluator)
        ast_root_node = self.create_ast(tokens)
        result = self.parse_node(ast_root_node)

        print("\nResults")
        print(s)
        print("Expected: " + str(expected))
        print("AST:      " + str(result))


def test_exp(s, print_pass=True):
    expected = eval(s)
    try:
        actual = AST.parse(s)
    except Exception:
        actual = None

    if expected != actual:
        print("FAIL: " + s + " --> " + str(expected) + ", got " + str(actual))
        return False
    elif print_pass:
        print("PASS: " + s + " --> " + str(actual))

    return True


def test_fuzzy():
    digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

    ops = ["+", "-", "*", "/"]

    iterations = 100

    fail_count = 0
    for i in range(iterations):
        s = ""
        for _ in range(50):
            s += random.choice(digits)
            s += random.choice(ops)

        s = s[:-1]
        r = test_exp(s, False)
        if not r:
            fail_count += 1

    pass_count = iterations - fail_count
    print("Results: " + str(pass_count) + "/" + str(iterations) + " PASSED")


def test_custom():
    expressions = [
        "1+2**2*8",
        "-5*-2+-4/-3**2+2**-2",
        "5*(3+4)",
        "3/(5+(2**2)*4-(-4*3+3*(3/4+(4+5+4+4))))",
        "-5+6*2**(6-4)",
        "-(5--6)",
    ]

    fail_count = 0
    for exp in expressions:
        r = test_exp(exp)
        if not r:
            fail_count += 1

    total = len(expressions)
    pass_count = total - fail_count
    print("Results: " + str(pass_count) + "/" + str(total) + " PASSED")


def test_suite():
    print("\nTest Suite")
    print("\nFuzzy")
    test_fuzzy()
    print("\nCustom")
    test_custom()


if __name__ == '__main__':
    ast = AST()
    ast.run()
    test_suite()
