from dataclasses import dataclass
from enum import Enum

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
                        literal = tokens[i + 2]
                        if literal.type != TokenType.INT_LITERAL:
                            raise Exception("Expected literal")
                        # var assembly
                        self.assembly_lines.append("VAR " + id_name)
                        self.assembly_lines.append("MOVLW " + literal.value)
                        self.assembly_lines.append("MOVWF " + id_name)
                        i += 3
                    elif next_t.type == TokenType.SCOPE and next_t.value == "(":
                        if tokens[i + 2].type != TokenType.SCOPE:
                            raise NotImplemented  # input args
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
