import json
from pathlib import Path

import click

from factorio_microcontroller import factorio_compiler
from factorio_microcontroller_simulator.instruction_executor import MicrocontrollerState, InstructionExecutor

RESOURCE_FOLDER = Path(__file__).parent.parent / "resources"


class FactorioMicrocontrollerSim:
    def __init__(self, file_name):
        self.binary = self.load_binary(file_name)
        self.opcode_map = self.load_opcode_map()

        self.instruction_executor = InstructionExecutor()

    def load_binary(self, file_name):
        with open(file_name) as f:
            return f.read().splitlines()

    def simulate(self):
        microcontroller_state = MicrocontrollerState(0, dict())
        program_counter = 1

        while True:
            instruction = self.binary[program_counter-1]
            opcode, literal = self.decode_instruction(instruction)

            self.instruction_executor.execute(opcode, literal, microcontroller_state)

            program_counter += 1


    def decode_instruction(self, line):
        literal_binary = line[:24]
        opcode_binary = line[24:]

        literal = int(literal_binary, 2)
        opcode = self.opcode_map[int(opcode_binary, 2)]

        return opcode, literal

    def load_opcode_map(self):
        with open(RESOURCE_FOLDER / "opcodes.json") as opcode_file:
            opcodes = json.loads(opcode_file.read())

        opcodes_expanded = dict()
        for opcode in opcodes:
            binary = opcodes[opcode]
            if len(binary) == 4:
                for i in range(16):
                    binary = opcodes[opcode] + '{0:04b}'.format(i)
                    opcodes_expanded[opcode + str(i)] = int(binary, 2)
            else:
                opcodes_expanded[opcode] = int(binary, 2)

        return {v: k for k, v in opcodes_expanded.items()}


@click.command()
@click.option('--binary', '-b', help='Name of the binary file')
@click.option('--assembly', '-a', help='Name of the assembly file')
def main(binary, assembly):
    if binary:
        factorio_microcontroller_sim = FactorioMicrocontrollerSim(binary)
        factorio_microcontroller_sim.simulate()
    else:
        compiler = factorio_compiler.FactorioCompiler()
        binary_file = assembly[:-4] + '_binary.txt'
        compiler.compile_to_bin(assembly, binary_file)
        factorio_microcontroller_sim = FactorioMicrocontrollerSim(binary_file)
        factorio_microcontroller_sim.simulate()


if __name__ == '__main__':
    main()
