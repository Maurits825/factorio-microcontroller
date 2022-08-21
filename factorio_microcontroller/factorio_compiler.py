import json
import click
from pathlib import Path

RESOURCE_FOLDER = Path(__file__).parent.parent / "resources"

#TODO create a loggin class and stuff to print line and stuff like that

class FactorioCompiler:
    def __init__(self):
        with open(RESOURCE_FOLDER / "opcodes.json") as opcodes:
            self.opcodes = json.loads(opcodes.read())

    def compile_to_bin(self, file_name):
        with open(file_name) as f:
            assembly_program_raw = f.read().splitlines()

        assembly_program = self.remove_comments_and_blank_lines(assembly_program_raw)

        assembly_program = self.add_var_to_functions_input_args(assembly_program)

        functions = self.calculate_function_address(assembly_program)

        binary_with_call, function_binary = self.decode_instructions(assembly_program)

        # add halt between program memory and function memory
        binary_with_call += ['{0:032b}'.format(0)]
        program_size = len(binary_with_call)
        binary_with_call += function_binary

        final_binary = self.add_function_binary(binary_with_call, functions, program_size)

        binary_file_name = file_name[:-4] + '.bin'
        with open(binary_file_name, 'w') as f:
            f.write('\n'.join(line for line in final_binary))

        return binary_file_name

    def remove_comments_and_blank_lines(self, assembly):
        assembly_stripped = []
        for line in assembly:
            if line and '#' not in line:
                assembly_stripped.append(line.rstrip())

        return assembly_stripped

    def calculate_function_address(self, assembly):
        functions = dict()
        program_function_address = 0
        counting = False
        for line in assembly:
            if 'FN' in line:
                function_name = line.split()[1]
                functions[function_name] = program_function_address
                counting = True
            elif 'END' in line:
                counting = False
            # skip goto labels
            elif len(line) == 1:
                pass
            elif counting:
                program_function_address += 1
            else:
                pass
        if counting:
            print('Missing RET statement in function: ' + function_name)
            exit()

        return functions

    def add_function_binary(self, binary_with_call, functions, program_size):
        final_binary = []
        for line in binary_with_call:
            if 'CALL' in line:
                opcode = self.opcodes['CALL']
                literal = '{0:024b}'.format(functions[line.split()[1]] + program_size + 1)
                final_binary.append(literal + opcode)
            else:
                final_binary.append(line)
        return final_binary

    def decode_instructions(self, assembly):
        binary_with_call = []
        function_binary = []
        current_binary = binary_with_call

        global_goto_map = dict()
        current_goto_map = global_goto_map

        global_variables_map = dict()
        current_variable_map = global_variables_map

        global_variable_address = [1]
        current_variable_address = global_variable_address

        for line in assembly:
            instructions = line.split()
            mnemonic = instructions[0]

            if mnemonic == 'CALL':
                if len(instructions) > 2:
                    self.handle_input_arguments(instructions, current_variable_map, current_variable_address, current_binary)

                current_binary.append(line)

            elif mnemonic == 'FN':
                function_goto_map = dict()
                current_goto_map = function_goto_map

                function_variable_map = dict()
                current_variable_map = function_variable_map

                current_variable_address = [1]

                current_binary = function_binary

                # load input args
                if len(instructions) > 2:
                    for variable in instructions[2:]:
                        current_variable_map[variable] = current_variable_address[0]
                        current_variable_address[0] += 1

            elif len(instructions) == 1 and mnemonic not in self.opcodes:
                if mnemonic != 'END':
                    current_goto_map[mnemonic] = len(binary_with_call) + 1
            else:
                opcode = self.get_opcode(mnemonic)
                literal = self.get_literal(mnemonic, instructions, current_goto_map, current_variable_map,
                                           current_variable_address)
                current_binary.append(literal + opcode)

            # switch back scopes if returning from function
            if 'END' in mnemonic:
                current_goto_map = global_goto_map
                current_variable_map = global_variables_map
                current_variable_address = global_variable_address
                current_binary = binary_with_call
                continue

        return binary_with_call, function_binary

    def get_opcode(self, mnemonic):
        if 'EQ' in mnemonic or 'LESS' in mnemonic or 'GRT' in mnemonic:
            mnemonic_split = mnemonic.split(',')
            opcode = self.opcodes[mnemonic_split[0]] + '{0:04b}'.format(int(mnemonic_split[1]))
        else:
            opcode = self.opcodes[mnemonic]

        return opcode

    def get_literal(self, mnemonic, instructions, goto_map, variables, variable_address):
        if mnemonic == 'RET' or mnemonic == 'PULSE':
            literal = '{0:024b}'.format(0)
        else:
            literal = self.get_literal_from_operand(mnemonic, instructions[1], goto_map, variables, variable_address)

        return literal

    def get_literal_from_operand(self, mnemonic, operand, goto_map, variables, variable_address):
        literal = self.get_literal_value_from_operand(operand)
        if not literal:
            if mnemonic == 'GOTO':
                if operand in goto_map:
                    literal = '{0:024b}'.format(goto_map[operand])
                else:
                    print('GOTO label ' + operand + ' does not exist.')
                    exit()
            elif mnemonic == 'VAR':
                if operand in variables:
                    print('Variable ' + operand + ' already exists.')
                    exit()
                else:
                    variables[operand] = variable_address[0]
                    variable_address[0] += 1
                    literal = '{0:024b}'.format(variables[operand])
            else:
                if operand in variables:
                    literal = '{0:024b}'.format(variables[operand])
                else:
                    print('Variable ' + operand + ' does not exist.')
                    exit()
        if literal:
            return literal
        else:
            print('Error with literal')
            exit()

    def get_literal_value_from_operand(self, operand):
        # TODO we can still hard code memory addresses? could check this and give an error
        literal = None

        if '0b' in operand:
            literal = operand.replace('0b', '')
        elif '0x' in operand:
            literal = '{0:024b}'.format(int(operand, 16))
        elif '0d' in operand:
            literal = '{0:024b}'.format(int(operand.replace('0d', '')))

        return literal

    def handle_input_arguments(self, instructions, variable_map, variable_address, current_binary):
        for index, operand in enumerate(instructions[2:]):
            # Move value to W
            if operand in variable_map:
                opcode = self.get_opcode('MOVFW')
                literal = '{0:024b}'.format(variable_map[operand])
            else:
                opcode = self.get_opcode('MOVLW')
                literal = self.get_literal_value_from_operand(operand)
                if not literal:
                    print("Unknown input argument " + str(operand) + " to function " + str(instructions[1]))
                    exit()

            current_binary.append(literal + opcode)

            # Move W to the input variable
            opcode = self.get_opcode('MOVWF')
            literal = '{0:024b}'.format(variable_address[0] + index)
            current_binary.append(literal + opcode)

    def add_var_to_functions_input_args(self, assembly):
        new_assembly = []
        for line in assembly:
            new_assembly.append(line)
            if "FN" in line:
                instructions = line.split()
                if len(instructions) > 2:
                    input_variable_count = len(instructions) - 2
                    new_assembly.append('VAR 0d' + str(input_variable_count))

        return new_assembly


@click.command()
@click.option('--assembly', '-a', help='Assembly file')
def main(assembly):
    factorio_compiler = FactorioCompiler()
    factorio_compiler.compile_to_bin(assembly)


if __name__ == '__main__':
    main()
