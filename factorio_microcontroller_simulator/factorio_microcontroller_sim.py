import json
from pathlib import Path

import click

from instruction_executor import InstructionExecutor, MicrocontrollerState

RESOURCE_FOLDER = Path(__file__).parent.parent / "resources"


class FactorioMicrocontrollerSim:
    def __init__(self, file_name):
        self.binary = self.load_binary(file_name)
        self.opcode_map = self.load_opcode_map()
        self.decoded_instructions = self.decode_all_instructions()

        self.instruction_executor = InstructionExecutor()

    def load_binary(self, file_name):
        with open(file_name) as f:
            return f.read().splitlines()

    def simulate(self):
        microcontroller_state = MicrocontrollerState()

        while True:
            opcode, literal = self.decoded_instructions[microcontroller_state.program_counter-1]
            is_halt = self.instruction_executor.execute(opcode, literal, microcontroller_state)

            print("Program count: " + str(microcontroller_state.program_counter))
            print("Output register: " + str(microcontroller_state.output_registers))

            if is_halt:
                return microcontroller_state

    def decode_all_instructions(self):
        decoded_instructions = []
        for instruction in self.binary:
            decoded_instructions.append(self.decode_instruction(instruction))
        return decoded_instructions

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
def main(binary,):
    factorio_microcontroller_sim = FactorioMicrocontrollerSim(binary)
    factorio_microcontroller_sim.simulate()


if __name__ == '__main__':
    main()
