import json
import re

import click
from pathlib import Path

from factorio_compiler.assembly_line import AssemblyLine, AssemblyToken
from factorio_compiler.preprocessor import Preprocessor
from factorio_compiler.token_type import TokenType

RESOURCE_FOLDER = Path(__file__).parent.parent / "resources"

RESERVED_IDENTIFIERS = [
    "LABEL", "FN"
]


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

    def compile(self, file_name):
        with open(file_name) as f:
            raw_assembly_lines = f.read().splitlines()

        assembly_lines = self.get_assembly_lines(raw_assembly_lines)
        Preprocessor.preprocess(assembly_lines)
        scoped_assembly_lines = self.split_scopes(assembly_lines)

        # TODO we want to have the main and functions the same so that we then just have one fn run on them?
        # we need to be able to resolve gotos and fn calls -> have to expand FN and CALL, and remove LABEL
        # then can count and create goto and call maps with program counter
        # TODO remove goto labels, split functions, add VAR for input -> we want to be able to resolve call and goto
        # first split functions
        a = 2

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
        scoped_lines = {"main": [], "functions": []}

        current_scope = scoped_lines["main"]
        for assembly_line in assembly_lines:
            if 'FN' in assembly_line.line:
                current_scope = scoped_lines["functions"]
                current_scope.append(assembly_line)
            elif 'RET' in assembly_line.line:
                current_scope.append(assembly_line)
                current_scope = scoped_lines["main"]
            else:
                current_scope.append(assembly_line)

        return scoped_lines

    # def split_function


@click.command()
@click.option('--assembly-file', '-a', help='Assembly file')
def main(assembly_file):
    assembly_compiler = AssemblyCompiler()
    assembly_compiler.compile(assembly_file)


if __name__ == '__main__':
    main()
