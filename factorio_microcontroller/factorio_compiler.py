import json
import click


OPCODES_FILE = "../resources/opcodes.json"


class FactorioCompiler:
    def __init__(self):
        pass

    #TODO rewrite to remove duplicate code, make if branching simpler
    def compile_to_bin(self, file_name, binary_file_name):
        assembly_program_raw = []
        with open(file_name) as f:
            assembly_program_raw = f.read().splitlines()

        with open(OPCODES_FILE) as opcodes:
            opcodes = json.loads(opcodes.read())

        # remove comments/empty line
        # find variables
        assembly_program = []
        variables = dict()
        for line in assembly_program_raw:
            if line and '#' not in line:
                if '%' in line:
                    line_split = line.rstrip().split()
                    variables[line_split[1]] = line_split[2].replace('0b', '')
                else:
                    assembly_program.append(line.rstrip())

        # do a CALL/FN pass
        functions = dict()
        program_function_address = 0
        counting = False
        for line in assembly_program:
            if 'FN' in line:
                function_name = line.split()[1]
                functions[function_name] = program_function_address
                counting = True
            elif 'RET' in line:
                program_function_address += 1
                counting = False
            #skip goto labels
            elif len(line) == 1:
                pass
            elif counting:
                program_function_address += 1
            else:
                pass
        if counting:
            print('Missing RET statement')
            exit()


        #TODO variables in function scope?
        binary_with_call = []
        function_binary = []
        current_binary = binary_with_call

        global_goto_map = dict()
        current_goto_map = global_goto_map
        for line in assembly_program:
            instructions = line.split()
            mnemonic = instructions[0]
            # TODO operand is literal?
            if 'RET' in mnemonic:
                if mnemonic == 'RET':
                    literal = '{0:024b}'.format(0)
                else:
                    literal = self.get_literal(mnemonic, instructions[1], current_goto_map, variables)
                current_binary.append(literal + opcodes[mnemonic])
                current_goto_map = global_goto_map
                current_binary = binary_with_call
                continue
            elif len(instructions) > 1:
                operand = instructions[1]

            elif 'PULSE' in mnemonic:  #TODO better way to do this whole decoding thing
                operand = instructions[1]
            else:
                current_goto_map[mnemonic] = len(binary_with_call) + 1
                continue

            # function call address calculated later
            if 'CALL' in mnemonic:
                current_binary.append(line)
                continue

            if 'EQ' in mnemonic or 'LESS' in mnemonic or 'GRT' in mnemonic:
                mnemonic_split = mnemonic.split(',')
                opcode = opcodes[mnemonic_split[0]] + '{0:04b}'.format(int(mnemonic_split[1]))
            elif 'FN' in mnemonic:
                function_goto_map = dict()
                current_goto_map = function_goto_map
                current_binary = function_binary
                continue
            else:
                opcode = opcodes[mnemonic]

            literal = self.get_literal(mnemonic, operand, current_goto_map, variables)

            current_binary.append(literal + opcode)

        binary_with_call += ['{0:032b}'.format(0)]
        program_size = len(binary_with_call)
        binary_with_call += function_binary
        final_binary = []
        for line in binary_with_call:
            if 'CALL' in line:
                opcode = opcodes['CALL']
                literal = '{0:024b}'.format(functions[line.split()[1]] + program_size + 1)
                final_binary.append(literal + opcode)
            else:
                final_binary.append(line)

        with open(binary_file_name, 'w') as f:
            f.write('\n'.join(line for line in final_binary))

    def get_literal(self, mnemonic, operand, goto_map, variables):
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
