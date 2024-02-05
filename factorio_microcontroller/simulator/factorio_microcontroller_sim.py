from copy import deepcopy

import click

from compiler.assembly_compiler import AssemblyCompiler, DisassemblerInfo
from simulator.context_state import ContextState
from simulator.igpu_sim import IGPUSim
from simulator.input_sim import InputSim
from simulator.instruction_decoder import InstructionDecoder
from simulator.instruction_executor import InstructionExecutor
from simulator.microcontroller_state import MicrocontrollerState

CPU_BASE_SPEED = 0.375
CYCLE_TIMEOUT = 50_000


class FactorioMicrocontrollerSim:
    def __init__(self, file_name, disassembler_info: DisassemblerInfo = None):
        self.disassembler_info = disassembler_info
        self.binary = self.load_binary(file_name)

        self.instruction_executor = InstructionExecutor()
        self.igpu_sim = IGPUSim()

    def load_binary(self, file_name):
        with open(file_name) as f:
            return f.read().splitlines()

    def run(self, verbose, enable_igpu_sim):
        decoded_instructions = InstructionDecoder.decode_all_instructions(self.binary)
        self.simulate(decoded_instructions, verbose, enable_igpu_sim)

        if enable_igpu_sim:
            self.igpu_sim.run()

    def simulate(self, decoded_instructions, verbose, enable_igpu_sim):
        microcontroller_state = MicrocontrollerState()
        cycle_count = 0
        while True:
            opcode, literal = decoded_instructions[microcontroller_state.program_counter - 1]

            # TODO maybe a json config with the input mock type and data (linear, random, exponential)
            microcontroller_state.input_values[0] = InputSim.get_linear_input(cycle_count, 2, 0)

            is_halt = self.instruction_executor.execute(opcode, literal, microcontroller_state)
            self.update_context_state(microcontroller_state)

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

    def update_context_state(self, microcontroller_state: MicrocontrollerState):
        if not self.disassembler_info:
            return

        # find scope
        current_scope = None
        for scope, address in self.disassembler_info.function_addresses.items():
            if (microcontroller_state.program_counter - 1) < address:
                break
            current_scope = scope

        scope_line_number = (microcontroller_state.program_counter - 1 -
                             self.disassembler_info.function_addresses[current_scope])
        try:
            assembly_line = self.disassembler_info.function_scopes[current_scope][scope_line_number]
        except IndexError:
            return

        variables = dict()
        for variable_name, address in self.disassembler_info.variable_addresses[current_scope].items():
            variables[variable_name] = microcontroller_state.read_f_memory(address)

        context_state = ContextState(
            line_number=assembly_line.line_number,
            line=assembly_line.raw_line,
            scope=current_scope,
            variables=variables
        )

        microcontroller_state.context_state = context_state

    @staticmethod
    def print_verbose(opcode, literal, cycle_count, microcontroller_state):
        print("\nCycle: " + str(cycle_count))
        print("Program count: " + str(microcontroller_state.program_counter - 1))

        if microcontroller_state.context_state:
            context = microcontroller_state.context_state
            print("Line: " + str(context.line_number) + ". " + context.line)
            print("Opcode: " + str(opcode) + ", literal: " + str(literal))
            print("Output & W registers: " + str(microcontroller_state.output_registers) +
                  ", " + str(microcontroller_state.w_register))
            print("Scope: " + context.scope + ", Variables: " + str(context.variables))
        else:
            print("Opcode: " + str(opcode) + ", literal: " + str(literal))
            print("Output & W registers: " + str(microcontroller_state.output_registers) +
                  ", " + str(microcontroller_state.w_register))
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
    if binary:
        binary_file_name = binary
        factorio_microcontroller_sim = FactorioMicrocontrollerSim(binary_file_name)
    else:
        compiler = AssemblyCompiler()
        binary_file_name, disassembler_info = compiler.compile(assembly)
        factorio_microcontroller_sim = FactorioMicrocontrollerSim(binary_file_name, disassembler_info)

    factorio_microcontroller_sim.run(verbose, enable_igpu_sim)


if __name__ == '__main__':
    main()
