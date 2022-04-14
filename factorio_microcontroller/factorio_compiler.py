import json
import click


OPCODES_FILE = "../resources/opcodes.json"


class FactorioCompiler:
    def __init__(self):
        with open(OPCODES_FILE) as opcodes:
            self.opcodes = json.loads(opcodes.read())

    def compile_to_bin(self, file_name, binary_file_name):
        with open(file_name) as f:
            assembly_program_raw = f.read().splitlines()

        # find variables TODO remove comment later
        assembly_program, variables = self.remove_comments_and_blank_lines(assembly_program_raw)

        functions = self.calculate_function_address(assembly_program)

        #TODO variables in function scope?
        binary_with_call, function_binary = self.decode_instructions(assembly_program, variables)

        # add halt between program memory and function memory
        binary_with_call += ['{0:032b}'.format(0)]
        program_size = len(binary_with_call)
        binary_with_call += function_binary

        final_binary = self.add_function_binary(binary_with_call, functions, program_size)

        with open(binary_file_name, 'w') as f:
            f.write('\n'.join(line for line in final_binary))

    def remove_comments_and_blank_lines(self, assembly):
        variables = dict()
        assembly_stripped = []
        for line in assembly:
            if line and '#' not in line:
                if '%' in line:
                    #TODO remove this, vars will be handled differently in the future
                    line_split = line.rstrip().split()
                    variables[line_split[1]] = line_split[2].replace('0b', '')
                else:
                    assembly_stripped.append(line.rstrip())

        return assembly_stripped, variables

    def calculate_function_address(self, assembly):
        functions = dict()
        program_function_address = 0
        counting = False
        for line in assembly:
            if 'FN' in line:
                function_name = line.split()[1]
                functions[function_name] = program_function_address
                counting = True
            elif 'RET' in line:
                program_function_address += 1
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

    def decode_instructions(self, assembly, variables):
        # TODO variables in function scope?
        binary_with_call = []
        function_binary = []
        current_binary = binary_with_call

        global_goto_map = dict()
        current_goto_map = global_goto_map
        for line in assembly:
            instructions = line.split()
            mnemonic = instructions[0]

            # decode call later
            if mnemonic == 'CALL':
                current_binary.append(line)
            elif mnemonic == 'FN':
                function_goto_map = dict()
                current_goto_map = function_goto_map
                current_binary = function_binary
            elif len(instructions) == 1 and mnemonic not in self.opcodes:
                current_goto_map[mnemonic] = len(binary_with_call) + 1
            else:
                opcode = self.get_opcode(mnemonic)
                literal = self.get_literal(mnemonic, instructions, current_goto_map, variables)
                current_binary.append(literal + opcode)

            # switch back scopes if returning from function
            if 'RET' in mnemonic:
                current_goto_map = global_goto_map
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

    def get_literal(self, mnemonic, instructions, goto_map, variables):
        literal = None
        if mnemonic == 'RET' or mnemonic == 'PULSE':
            literal = '{0:024b}'.format(0)
        elif len(instructions) > 1: #TODO change to just else maybe when it works?
            literal = self.get_literal_from_operand(mnemonic, instructions[1], goto_map, variables)
        else:
            print("Error getting literal from: " + instructions)
            exit()

        return literal

    def get_literal_from_operand(self, mnemonic, operand, goto_map, variables):
        literal = None
        if '0b' in operand:
            literal = operand.replace('0b', '')
        else:
            if 'GOTO' in mnemonic:
                if operand in goto_map:
                    literal = '{0:024b}'.format(goto_map[operand])
                else:
                    print('GOTO label ' + operand + ' does not exist.')
                    exit()
            else:
                if operand in variables:
                    literal = variables[operand]
                else:
                    print('Variable ' + operand + ' does not exist.')
                    exit()
        if literal:
            return literal
        else:
            print('Error with literal')
            exit()


@click.command()
@click.option('--assembly', '-a', help='Assembly file')
@click.option('--binary', '-b', help='Name of the output binary file')
def main(assembly, binary):
    factorio_compiler = FactorioCompiler()
    factorio_compiler.compile_to_bin(assembly, binary)


if __name__ == '__main__':
    main()
