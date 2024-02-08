import json
import re
from dataclasses import dataclass

import click
from pathlib import Path

from compiler.assembly_line import AssemblyLine, AssemblyToken
from compiler.binary_line import BinaryLine
from compiler.error_logger import ErrorLogger
from compiler.preprocessor import Preprocessor
from compiler.reserved_identifiers import RESERVED_IDENTIFIERS, ReservedIdentifier, MAIN_FUNCTION_NAME

from compiler.token_type import TokenType

RESOURCE_FOLDER = Path(__file__).parent.parent.parent / "resources"


@dataclass()
class DisassemblerInfo:
    function_scopes: dict[str, list[AssemblyLine]]
    function_addresses: dict[str, int]
    variable_addresses: dict[str, dict[str, int]]


class AssemblyCompiler:
    def __init__(self):
        with open(RESOURCE_FOLDER / "opcodes.json") as opcodes:
            opcodes = json.loads(opcodes.read())
            self.opcodes = self.create_opcode_table(opcodes)

    def create_opcode_table(self, opcodes) -> dict:
        all_opcodes = dict()
        for opcode in opcodes:
            binary = opcodes[opcode]
            if len(binary) == 4:
                for i in range(16):
                    binary = opcodes[opcode] + '{0:04b}'.format(i)
                    all_opcodes[opcode + "," + str(i)] = binary
            else:
                all_opcodes[opcode] = binary
        return all_opcodes

    def compile(self, file_name) -> (str, DisassemblerInfo):
        with open(file_name) as f:
            raw_assembly_lines = f.read().splitlines()

        assembly_lines = self.get_assembly_lines(raw_assembly_lines)
        Preprocessor.preprocess(assembly_lines)
        function_scopes = self.split_scopes(assembly_lines)

        # remove FN and END lines
        for function_name in function_scopes.keys():
            if function_name != MAIN_FUNCTION_NAME:
                del function_scopes[function_name][0]
                del function_scopes[function_name][-1]

        goto_map = self.get_goto_map(function_scopes)
        function_addresses = self.get_function_addresses(function_scopes)
        variable_map = self.get_variables_map(function_scopes)

        binary_lines = self.get_binary_lines(function_scopes, goto_map, function_addresses, variable_map)
        binary_file_name = file_name[:-4] + '.bin'
        with open(binary_file_name, 'w') as f:
            f.write('\n'.join(binary_line.binary for binary_line in binary_lines))

        disassembler_info = DisassemblerInfo(function_scopes, function_addresses, variable_map)
        return binary_file_name, disassembler_info

    def get_assembly_lines(self, raw_assembly_lines: list[str]) -> list[AssemblyLine]:
        assembly_lines = []
        for line_number, raw_line in enumerate(raw_assembly_lines):
            if not raw_line or re.match(r"^\s*\/\/", raw_line):
                continue

            line = re.sub(r"\/\/.*$", '', raw_line).strip()
            try:
                assembly_token = self.get_assembly_token(line)
            except ValueError:
                raise Exception("Unknown token: " + line + ". Line number: " + str(line_number + 1))

            assembly_line = AssemblyLine(
                raw_line=raw_line,
                line_number=line_number + 1,
                line=line,
                assembly_token=assembly_token,
            )

            assembly_lines.append(assembly_line)

        return assembly_lines

    def get_assembly_token(self, line: str) -> AssemblyToken:
        values = line.split()
        keyword = values[0]

        if re.match(r"^#", keyword):
            token_type = TokenType.PREPROCESSOR
        elif keyword in self.opcodes:
            token_type = TokenType.ASSEMBLY_INSTRUCTION
        elif keyword in RESERVED_IDENTIFIERS:
            token_type = TokenType.RESERVED_IDENTIFIER
        else:
            raise ValueError

        arguments = values[1:]
        return AssemblyToken(token_type, keyword, arguments)

    def split_scopes(self, assembly_lines: list[AssemblyLine]) -> dict[str, list[AssemblyLine]]:
        function_scopes = {MAIN_FUNCTION_NAME: []}

        current_scope = function_scopes[MAIN_FUNCTION_NAME]
        for assembly_line in assembly_lines:
            if assembly_line.assembly_token.keyword == ReservedIdentifier.FUNCTION.value:
                if len(assembly_line.assembly_token.arguments) != 1:
                    raise Exception(ErrorLogger.format_error("Syntax error", assembly_line.line, assembly_line))
                function_name = assembly_line.assembly_token.arguments[0]
                function_scopes[function_name] = []
                current_scope = function_scopes[function_name]
                current_scope.append(assembly_line)
            elif assembly_line.assembly_token.keyword == ReservedIdentifier.FUNCTION_END.value:
                current_scope.append(assembly_line)
                current_scope = function_scopes[MAIN_FUNCTION_NAME]
            else:
                current_scope.append(assembly_line)

        return function_scopes

    def get_goto_map(self, function_scopes: dict[str, list[AssemblyLine]]):
        goto_map = dict()
        for function_name, assembly_lines in function_scopes.items():
            function_goto = dict()
            count = 0
            for assembly_line in assembly_lines[:]:
                token = assembly_line.assembly_token
                if token.keyword == ReservedIdentifier.GOTO_LABEL.value:
                    function_goto[token.arguments[0]] = count
                    assembly_lines.remove(assembly_line)
                else:
                    count += 1
            goto_map[function_name] = function_goto
        return goto_map

    def get_function_addresses(self, function_scopes: dict[str, list[AssemblyLine]]):
        function_addresses = dict()
        function_addresses[MAIN_FUNCTION_NAME] = 1
        current_address = len(function_scopes[MAIN_FUNCTION_NAME]) + 2
        for function_name, assembly_lines in function_scopes.items():
            if function_name == MAIN_FUNCTION_NAME:
                continue
            function_addresses[function_name] = current_address
            current_address += len(assembly_lines)
        return function_addresses

    def get_variables_map(self, function_scopes: dict[str, list[AssemblyLine]]):
        variables_map = dict()
        for function_name, assembly_lines in function_scopes.items():
            function_variables = dict()
            address = 1
            for assembly_line in assembly_lines:
                token = assembly_line.assembly_token
                if token.keyword == 'VAR':
                    variable_name = token.arguments[0]
                    if variable_name in function_variables:
                        raise Exception(ErrorLogger.format_error("Duplicate variable", variable_name, assembly_line))
                    function_variables[variable_name] = address
                    address += 1
            variables_map[function_name] = function_variables
        return variables_map

    def get_binary_lines(self, function_scopes, goto_map, function_addresses, variable_map) -> list[BinaryLine]:
        binary_map = dict()
        for function_name, assembly_lines in function_scopes.items():
            function_binary = []
            for assembly_line in assembly_lines:
                instruction_binary = self.opcodes[assembly_line.assembly_token.keyword]
                literal = self.get_literal(assembly_line, function_addresses[function_name], function_addresses,
                                           goto_map[function_name], variable_map[function_name])
                binary_line = BinaryLine(literal + instruction_binary, assembly_line)
                function_binary.append(binary_line)
            binary_map[function_name] = function_binary

        all_binary_lines = [binary_line for binary_line in binary_map[MAIN_FUNCTION_NAME]]
        # add halt between program memory and function memory
        all_binary_lines.append(BinaryLine('{0:032b}'.format(0), None))

        for function_name, binary_lines in binary_map.items():
            if function_name == MAIN_FUNCTION_NAME:
                continue
            for binary_line in binary_lines:
                all_binary_lines.append(binary_line)

        return all_binary_lines

    def get_literal(self, assembly_line: AssemblyLine, function_address, function_addresses, goto_map,
                    variables) -> str:
        token = assembly_line.assembly_token
        if not token.arguments:
            return '{0:024b}'.format(0)

        if token.keyword == 'GOTO':
            label = token.arguments[0]
            if label in goto_map:
                literal = goto_map[label] + function_address
                return '{0:024b}'.format(literal)
            else:
                raise Exception(ErrorLogger.format_error("GOTO label does not exist", label, assembly_line))

        argument = token.arguments[0]

        if argument in variables:
            return '{0:024b}'.format(variables[argument])
        if argument in function_addresses:
            return '{0:024b}'.format(function_addresses[argument])

        if re.match(r"^0b", argument):
            return '{0:024b}'.format(int(argument.replace('0b', ''), 2))
        if re.match(r"^0x", argument):
            return '{0:024b}'.format(int(argument, 16))
        if re.match(r"\d*", argument):
            return '{0:024b}'.format(int(argument))

        raise Exception(ErrorLogger.format_error("Error with literal", argument, assembly_line))


@click.command()
@click.option('--assembly-file', '-a', help='Assembly file')
def main(assembly_file):
    assembly_compiler = AssemblyCompiler()
    assembly_compiler.compile(assembly_file)


if __name__ == '__main__':
    main()
