from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# TODO figure out proper imports
from lexer import Token
from lexer import TokenType


@dataclass
class ForLoop:
    max_count: int
    var: str
    goto_label: str


class ScopeType(Enum):
    FOR = 0
    FUNCTION = 1


@dataclass
class OperationNode:
    operand1: Token | 'OperationNode' | None
    operand2: Token | 'OperationNode' | None
    operator: str
    parent: 'OperationNode' | None


class OperationTreeState(Enum):
    OPERAND1 = 0
    OPERAND2 = 1
    OPERATOR = 2


OPERATORS = {"*": 0, "/": 0, "+": 1, "-": 1}


class Parser:
    def __init__(self):
        self.assembly_lines = []
        self.for_loop_stack = []
        self.scope_type_stack = []

    def run(self, tokens: list[Token]):
        self.assembly_lines = []
        self.for_loop_stack = []
        self.scope_type_stack = []

        self.assembly_lines.append("CALL main")

        i = 0
        while i < len(tokens):
            t = tokens[i]
            match t.type:
                case TokenType.NEW_LINE:
                    i += 1
                case TokenType.FUNCTION:
                    name_token = tokens[i + 1]
                    if tokens[i + 1].type != TokenType.IDENTIFIER:
                        raise Exception("Bad token")

                    self.assembly_lines.append("FN " + name_token.value)

                    # i + n is scuffed?
                    t = tokens[i + 2]
                    # better way to check all this
                    if not (t.type == TokenType.SCOPE and t.value == "("):
                        raise Exception("Expected arg list start")
                    # todo handle input args, well just one

                    t = tokens[i + 3]
                    if t.type == TokenType.IDENTIFIER:
                        self.assembly_lines.append("VAR " + t.value)
                        self.assembly_lines.append("MOVWF " + t.value)
                        i += 1

                    t = tokens[i + 3]
                    if not (t.type == TokenType.SCOPE and t.value == ")"):
                        raise Exception("Expected arg list end")

                    t = tokens[i + 4]
                    if not (t.type == TokenType.SCOPE and t.value == "{"):
                        raise Exception("Expected scope start")

                    self.scope_type_stack.append(ScopeType.FUNCTION)
                    i += 5

                case TokenType.IDENTIFIER:
                    id_name = t.value
                    # if we dont track specific keyword, we can check here?
                    # id could be var name declare/assign, fn call, ...?

                    if id_name == "asm":
                        # todo check syntax
                        self.assembly_lines.append(tokens[i + 2].value)
                        i += 4
                        continue

                    next_t = tokens[i + 1]
                    # TODO checking tokens, maybe add a fn
                    if next_t.type == TokenType.DEFINE and next_t.value == ":=":
                        nodes = self.unravel(tokens, i + 2)
                        literal = tokens[i + 2]
                        if literal.type != TokenType.INT_LITERAL:
                            raise Exception("Expected literal")
                        # var assembly
                        self.assembly_lines.append("VAR " + id_name)
                        self.assembly_lines.append("MOVLW " + literal.value)
                        self.assembly_lines.append("MOVWF " + id_name)
                        i += 3
                    elif next_t.type == TokenType.SCOPE and next_t.value == "(":
                        t = tokens[i + 2]
                        if t.type != TokenType.SCOPE:  # TODO assume its id, could also be literal
                            self.assembly_lines.append("MOVFW " + t.value)
                            i += 1
                        self.assembly_lines.append("CALL " + id_name)
                        i += 3

                case TokenType.FOR:
                    # todo assume correct syntax for now
                    loop_var = tokens[i + 1]
                    max_count = int(tokens[i + 4].value)

                    # todo make fn?
                    self.assembly_lines.append("VAR " + loop_var.value)
                    self.assembly_lines.append("MOVLW " + "0")  # start 0 for now
                    self.assembly_lines.append("MOVWF " + loop_var.value)

                    label_id = "loop1"  # todo manage these
                    self.assembly_lines.append("LABEL " + label_id)

                    self.for_loop_stack.append(
                        ForLoop(max_count, loop_var.value, label_id)
                    )

                    t = tokens[i + 5]
                    if not (t.type == TokenType.SCOPE and t.value == "{"):
                        raise Exception("Expected scope start at for loop")

                    self.scope_type_stack.append(ScopeType.FOR)
                    i += 6

                case TokenType.SCOPE:
                    if t.value != "}":
                        raise Exception("Should have consumed a scope start?")

                    scope = self.scope_type_stack.pop()
                    match scope:
                        case ScopeType.FOR:
                            for_loop = self.for_loop_stack.pop()
                            # check if i < max_count -> goto

                            self.assembly_lines.append("INCRF " + str(for_loop.var))
                            self.assembly_lines.append("MOVLW " + str(for_loop.max_count))
                            self.assembly_lines.append("GRTWF,0 " + for_loop.var)
                            self.assembly_lines.append("GOTO " + for_loop.goto_label)

                        case ScopeType.FUNCTION:
                            # TODO could check if all code path return
                            # or just always have it in case?
                            self.assembly_lines.append("RET")
                            self.assembly_lines.append("END")

                    i += 1

        for line in self.assembly_lines:
            print(line)

        return self.assembly_lines

    # todo maybe store i as state in parser or another class?
    def unravel(self, tokens: list[Token], start: int,  break_on=TokenType.NEW_LINE) -> (OperationNode, int):
        i = start
        state = OperationTreeState.OPERAND1
        working_node = OperationNode(None, None, "", None)
        last_op = 0

        root_node = working_node
        last_node = None

        while i < len(tokens):
            t = tokens[i]

            if t.type == TokenType.NEW_LINE == break_on:
                break
            if t.is_equal(TokenType.SCOPE, ")") and t.type == break_on:
                break
            if (t.type == TokenType.NEW_LINE or t.is_equal(TokenType.SCOPE, ")")) and t.value != break_on:
                raise Exception("Unexpected new line or scope: " + str(t))

            match state:
                case OperationTreeState.OPERAND1:
                    if t.type == TokenType.INT_LITERAL:
                        working_node.operand1 = t
                    elif t.is_equal(TokenType.OPERATOR, "-") or t.is_equal(TokenType.OPERATOR, "+"):
                        is_negative, i = self.handle_unary_op(tokens, i)
                        if is_negative:
                            working_node.operand1 = Token(TokenType.INT_LITERAL, "-1")
                            working_node.operator = "*"
                            state = OperationTreeState.OPERAND2
                            continue
                    elif t.is_equal(TokenType.SCOPE, "("):
                        working_node.operand1, i = self.unravel(tokens, i+1, TokenType.SCOPE)
                    elif t.type == TokenType.IDENTIFIER:
                        if tokens[i + 1].is_equal(TokenType.SCOPE, "("):
                            raise Exception("TODO")
                        else:
                            working_node.operand1 = t
                    else:
                        raise Exception("Unexpected token in unravel: " + str(t))
                    state = OperationTreeState.OPERATOR

                case OperationTreeState.OPERAND2:
                    if t.type == TokenType.INT_LITERAL:
                        working_node.operand2 = t
                    elif t.is_equal(TokenType.OPERATOR, "-") or t.is_equal(TokenType.OPERATOR, "+"):
                        is_negative, i = self.handle_unary_op(tokens, i)
                        if is_negative:
                            if last_node:
                                last_node.operand2 = working_node
                            else:
                                root_node.operand2 = working_node
                            working_node = OperationNode(None, None, "", None)
                            working_node.operand1 = Token(TokenType.INT_LITERAL, "-1")
                            working_node.operator = "*"

                            if last_node:
                                last_node.operand2.operand2 = working_node
                            else:
                                root_node.operand2.operand2 = working_node
                            continue

                    elif t.is_equal(TokenType.SCOPE, "("):
                        working_node.operand2, i = self.unravel(tokens, i+1, TokenType.SCOPE)
                    elif t.type == TokenType.IDENTIFIER:
                        if tokens[i + 1].is_equal(TokenType.SCOPE, "("):
                            raise NotImplemented("TODO")
                        else:
                            working_node.operand2 = t
                    else:
                        raise Exception("Unexpected token in unravel: " + str(t))

                    last_node = working_node
                    working_node = OperationNode(None, None, "", None)
                    state = OperationTreeState.OPERATOR

                case OperationTreeState.OPERATOR:
                    current_op = OPERATORS[t.value]
                    if current_op < last_op:
                        working_node.operand1 = last_node.operand2
                        last_node.operand2 = working_node
                        working_node.parent = last_node
                    elif not working_node.operand1:
                        if current_op == last_op:
                            working_node.operand1 = last_node
                            if not last_node.parent:
                                root_node = working_node
                                working_node.parent = None
                            else:
                                last_node.parent.operand2 = working_node
                                working_node.parent = last_node.parent
                        else:
                            working_node.operand1 = root_node
                            # working_node.operand1.parent = root_node # todo we dont need this?
                            root_node = working_node

                    working_node.operator = t.value
                    last_op = OPERATORS[t.value]
                    state = OperationTreeState.OPERAND2

            i += 1

        return root_node, i

    def handle_unary_op(self, tokens: list[Token], start: int) -> (bool, int):
        is_negative = tokens[start].is_equal(TokenType.OPERATOR, "-")

        i = start + 1
        while i < len(tokens):
            t = tokens[i]
            if not t.is_equal(TokenType.OPERATOR, "-") and not t.is_equal(TokenType.OPERATOR, "+"):
                break

            if t.is_equal(TokenType.OPERATOR, "-"):
                is_negative = not is_negative

            i += 1

        return is_negative, i
