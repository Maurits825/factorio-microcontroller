import json
from copy import deepcopy
from pathlib import Path

import click

from compiler.assembly_compiler import AssemblyCompiler
from simulator.igpu_sim import IGPUSim
from simulator.input_sim import InputSim
from instruction_executor import InstructionExecutor, MicrocontrollerState

RESOURCE_FOLDER = Path(__file__).parent.parent.parent / "resources"
CPU_BASE_SPEED = 0.375
CYCLE_TIMEOUT = 50_000


class FactorioMicrocontrollerSim:
    def __init__(self, file_name):
        self.binary = self.load_binary(file_name)
        self.opcode_map = self.load_opcode_map()
        self.decoded_instructions = self.decode_all_instructions()

        self.instruction_executor = InstructionExecutor()
        self.igpu_sim = IGPUSim()

    def load_binary(self, file_name):
        with open(file_name) as f:
            return f.read().splitlines()

    def run(self, verbose, enable_igpu_sim):
        self.simulate(verbose, enable_igpu_sim)

        if enable_igpu_sim:
            self.igpu_sim.run()

    def simulate(self, verbose, enable_igpu_sim):
        microcontroller_state = MicrocontrollerState()
        cycle_count = 0
        while True:
            opcode, literal = self.decoded_instructions[microcontroller_state.program_counter - 1]

            # TODO maybe a json config with the input mock type and data (linear, random, exponential)
            microcontroller_state.input_values[0] = InputSim.get_linear_input(cycle_count, 2, 0)

            is_halt = self.instruction_executor.execute(opcode, literal, microcontroller_state)
            if enable_igpu_sim:
                self.igpu_sim.add_state(deepcopy(microcontroller_state.igpu_state))

            cycle_count += 1
            if cycle_count >= CYCLE_TIMEOUT:
                raise TimeoutError("Program did not halt after " + str(CYCLE_TIMEOUT) + " cycles.")

            if verbose:
                self.print_verbose(opcode, literal, cycle_count, microcontroller_state)

            if is_halt:
                print("\nHalted after " + str(cycle_count) + " cycles.")
                print("Would take " + str(round(cycle_count / (CPU_BASE_SPEED * 64))) + " seconds to complete.")
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

    @staticmethod
    def print_verbose(opcode, literal, cycle_count, microcontroller_state):
        print("\nCycle: " + str(cycle_count))
        print("Program count: " + str(microcontroller_state.program_counter - 1))
        print("Opcode: " + str(opcode) + ", literal: " + str(literal))
        print("Output & W registers: " + str(microcontroller_state.output_registers) +
              ", " + str(microcontroller_state.w_register))
        # TODO cant accurately display current scope without tracking it, will contain unallocated memory
        print("Current memory snapshot: " +
              str(microcontroller_state.f_memory[
                  microcontroller_state.variable_scope_stack[-1] + 1:
                  microcontroller_state.variable_scope_stack[-1] + 10]))
        print("Screen buffer: " + str(microcontroller_state.igpu_state.screen_buffer))


@click.command()
@click.option('--binary', '-b', help='Name of the binary file')
@click.option('--assembly', '-a', help='Name of the assembly file')
@click.option('--verbose', '-v', is_flag=True, show_default=True, default=False, help="Print out state information")
@click.option('--enable-igpu-sim', '-g', is_flag=True, show_default=True, default=False, help="Enable igpu sim")
def main(binary, assembly, verbose, enable_igpu_sim):
    if not binary:
        compiler = AssemblyCompiler()
        binary_file_name = compiler.compile(assembly)
    else:
        binary_file_name = binary

    factorio_microcontroller_sim = FactorioMicrocontrollerSim(binary_file_name)
    factorio_microcontroller_sim.run(verbose, enable_igpu_sim)


if __name__ == '__main__':
    main()
