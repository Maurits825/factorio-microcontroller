import click

from compiler.assembly_compiler import AssemblyCompiler
from lexer import Lexer
from parser import Parser


@click.command()
@click.option('--file', '-f', help='Name of the file')
def main(file):
    # TODO have another fn or class to handle the steps?
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
