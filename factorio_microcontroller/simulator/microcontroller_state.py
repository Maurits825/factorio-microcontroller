from dataclasses import dataclass

from simulator.constants import MEMORY_SIZE
from simulator.igpu_state import IGPUState


@dataclass()
class MicrocontrollerState:
    w_register: int
    f_memory: list
    program_counter: int
    function_call_stack: list
    variable_scope_stack: list
    variable_offset: int
    output_registers: list
    input_values: list
    igpu_state: IGPUState

    def __init__(self):
        self.w_register = 0
        self.f_memory = [0 for _ in range(MEMORY_SIZE)]
        self.program_counter = 1
        self.function_call_stack = []
        self.variable_scope_stack = [0]
        self.variable_offset = 0
        self.output_registers = [0, 0]
        self.input_values = [0, 0]
        self.igpu_state = IGPUState()

    def read_f_memory(self, address):
        return self.f_memory[address + self.variable_scope_stack[-1]]

    def write_f_memory(self, address, value):
        self.f_memory[address + self.variable_scope_stack[-1]] = value
