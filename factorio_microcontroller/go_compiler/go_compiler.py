import click

from compiler.assembly_compiler import AssemblyCompiler
from parser import Parser
from lexer import Lexer


@click.command()
@click.option('--file', '-f', help='Name of the file')
def main(file):
    lexer = Lexer()
    tokens = lexer.run(file)

    parser = Parser()
    assembly_lines = parser.run(tokens)

    assembly_file_name = "assembly.txt"
    with open(assembly_file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(assembly_lines))

    assembly_compiler = AssemblyCompiler()
    file, disassembler = assembly_compiler.compile(assembly_file_name)


if __name__ == '__main__':
    main()
