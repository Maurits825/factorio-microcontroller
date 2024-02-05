import click
import program_to_rom_blueprint
import pyperclip

from factorio_compiler.assembly_compiler import AssemblyCompiler


@click.command()
@click.option('--assembly', '-a', help='Name of the assembly file')
@click.option('--clipboard', '-c', help='Copy blueprint to the clipboard', is_flag=True)
def main(assembly, clipboard):
    compiler = AssemblyCompiler()
    binary_file = assembly[:-4] + '.bin'
    compiler.compile(assembly)

    binary2rom = program_to_rom_blueprint.Program2ROM()
    program = binary2rom.convert_file_to_base10_list(binary_file)
    program_rom_blueprint = binary2rom.convert_program_to_rom(program)
    if clipboard:
        pyperclip.copy(program_rom_blueprint)
        print('Program blueprint copied to clipboard')
    else:
        print('Blueprint:')
        print(program_rom_blueprint)


if __name__ == '__main__':
    main()
