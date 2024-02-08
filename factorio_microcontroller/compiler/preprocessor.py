import re

from compiler.assembly_line import AssemblyLine, AssemblyToken
from compiler.error_logger import ErrorLogger
from compiler.token_type import TokenType


class Preprocessor:
    @staticmethod
    def preprocess(assembly_lines: list[AssemblyLine]):
        defined_constants = dict()
        for assembly_line in assembly_lines[:]:
            token = assembly_line.assembly_token
            Preprocessor.replace_constants(defined_constants, token)

            if token.token_type == TokenType.PREPROCESSOR:
                value = token.arguments[1]

                if re.match(r"^EVPY", token.arguments[1]):
                    eval_argument = ''.join(token.arguments[1:])
                    try:
                        value = Preprocessor.eval_py_literal(eval_argument)
                    except ValueError:
                        raise Exception(ErrorLogger.format_error("Invalid char in EVPY", eval_argument, assembly_line))

                elif len(token.arguments) != 2:
                    raise Exception("Syntax error: " + assembly_line.line)

                defined_constants[token.arguments[0]] = str(value)
                assembly_lines.remove(assembly_line)

            elif token.arguments and re.match(r"^EVPY", token.arguments[0]):
                eval_argument = ''.join(token.arguments)
                try:
                    value = Preprocessor.eval_py_literal(eval_argument)
                except ValueError:
                    raise Exception(ErrorLogger.format_error("Invalid char in EVPY", eval_argument, assembly_line))
                else:
                    token.arguments = [value]

    @staticmethod
    def replace_constants(defined_constants: dict[str, str], token: AssemblyToken):
        for i, argument in enumerate(token.arguments):
            for constant in defined_constants.keys():
                if constant == argument:
                    token.arguments[i] = defined_constants[constant]
                elif re.search(r"(^|\W)" + constant + r"(\W|$)", argument):
                    token.arguments[i] = argument.replace(constant, defined_constants[constant])

    @staticmethod
    def eval_py_literal(eval_argument) -> str:
        eval_py = eval_argument.replace('EVPY', '')
        if re.match(r".*[A-Za-z]", eval_py):
            raise ValueError
        else:
            literal = int(eval(eval_py, {}))
            return str(literal)
