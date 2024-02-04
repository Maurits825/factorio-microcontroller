from factorio_compiler.assembly_line import AssemblyLine
from factorio_compiler.token_type import TokenType


class Preprocessor:
    @staticmethod
    def preprocess(assembly_lines: list[AssemblyLine]):
        defined_constants = dict()
        for assembly_line in assembly_lines[:]:
            token = assembly_line.assembly_token
            if token.token_type == TokenType.PREPROCESSOR:
                if len(token.arguments) != 2:
                    raise Exception("Syntax error: " + assembly_line.line)
                defined_constants[token.arguments[0]] = token.arguments[1]
                assembly_lines.remove(assembly_line)
            else:
                for i, argument in enumerate(token.arguments):
                    for constant in defined_constants.keys():
                        if constant == argument:
                            token.arguments[i] = defined_constants[constant]
