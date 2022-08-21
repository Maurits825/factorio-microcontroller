from dataclasses import dataclass
import re

MEMORY_SIZE = 500


@dataclass()
class MicrocontrollerState:
    w_register: int
    f_memory: []
    program_counter: int
    function_call_stack: []
    variable_scope_stack: []
    variable_offset: int
    output_registers: []

    def __init__(self):
        self.w_register = 0
        self.f_memory = [0 for _ in range(MEMORY_SIZE)]
        self.program_counter = 1
        self.function_call_stack = []
        self.variable_scope_stack = [0]
        self.variable_offset = 0
        self.output_registers = [0, 0]


ALU_OPERATIONS = [
    "ADD", "SUB", "MUL", "DIV",
    "MOD", "INCR", "DECR",
    "ROL", "ROR",
    "NAND", "NOR", "XOR",
]

BRANCHING_OPERATIONS = [
    "GRT", "LESS", "EQ",
    "CALL", "RET", "GOTO",
]

OTHER_OPERATIONS = [
    "NOP", "PULSE",
]


class InstructionExecutor:
    def execute(self, opcode: str, literal: int, state: MicrocontrollerState):
        if opcode == 'HALT':
            return True

        if any(alu_op in opcode for alu_op in ALU_OPERATIONS):
            self.execute_alu_operation(opcode, literal, state)

        elif any(branching_op in opcode for branching_op in BRANCHING_OPERATIONS):
            self.execute_branching_operation(opcode, literal, state)

        elif any(other_op in opcode for other_op in OTHER_OPERATIONS):
            self.execute_other_operation(opcode, literal, state)

        elif 'MOV' in opcode or opcode == 'VAR':
            self.execute_memory_operation(opcode, literal, state)

        elif 'WOUT' in opcode:
            self.execute_output_operation(opcode, literal, state)
        else:
            raise Exception("Unknown instruction.")

    def execute_other_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        if opcode == 'NOP':
            pass
        elif opcode == 'PULSE':
            pass

        state.program_counter += 1

    def execute_output_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        opcode_split = opcode.split(',')
        output_index = int(opcode_split[1]) - 1
        load = opcode_split[0][-1]

        if load == 'L':
            state.output_registers[output_index] = literal
        else:
            state.output_registers[output_index] = self.read_f_memory(literal, state)

        state.program_counter += 1

    def execute_branching_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        if any(conditional_op in opcode for conditional_op in ["GRT", "LESS", "EQ"]):
            input_a = state.w_register

            opcode_split = re.split(r'(\d+)', opcode)
            if opcode_split[0][-1] == 'F':
                input_b = self.read_f_memory(literal, state)
            else:
                input_b = literal

            skip = False
            if 'GRT' in opcode:
                if not (input_a > input_b):
                    skip = True
            elif 'LESS' in opcode:
                if not (input_a < input_b):
                    skip = True
            elif 'EQ' in opcode:
                if not (input_a == input_b):
                    skip = True
            else:
                raise Exception("Unknown branching operation.")

            if skip:
                skip_count = int(opcode_split[1])
                state.program_counter += skip_count + 2
            else:
                state.program_counter += 1

        elif opcode == 'CALL':
            state.function_call_stack.append(state.program_counter + 1)
            state.variable_scope_stack.append(state.variable_scope_stack[-1] +
                                              state.variable_offset)
            state.program_counter = literal

        elif opcode == 'GOTO':
            state.program_counter = literal

        elif 'RET' in opcode:
            if opcode == 'RETLW':
                state.w_register = literal
            elif opcode == 'RETFW':
                state.w_register = self.read_f_memory(literal, state)
            elif opcode == 'RET':
                pass
            else:
                raise Exception("Unknown return operation.")

            state.program_counter = state.function_call_stack.pop()
            state.variable_scope_stack.pop()

    def execute_memory_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        if opcode == 'VAR':
            state.variable_offset = literal
            state.program_counter += 1
            return

        elif opcode == 'MOVLW':
            store = 'w'
            address = 0
            value = literal
        elif opcode == 'MOVWF':
            store = 'f'
            address = literal
            value = state.w_register
        elif opcode == 'MOVFW':
            store = 'w'
            address = literal
            value = self.read_f_memory(address, state)
        elif opcode == 'MOVLF':
            store = 'f'
            address = state.w_register
            value = literal
        else:
            raise Exception("Unknown memory operation.")

        self.store_at_location(store, address, value, state)
        state.program_counter += 1

    def execute_alu_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        store, load = self.get_load_and_store_location(opcode)

        input_a = state.w_register
        input_b = self.load_from_location(load, literal, state)

        if 'ADD' in opcode:
            result = input_a + input_b
        elif 'SUB' in opcode:
            result = input_a - input_b
        elif 'MUL' in opcode:
            result = input_a * input_b
        elif 'DIV' in opcode:
            result = int(input_a / input_b)
        elif 'MOD' in opcode:
            result = int(input_a % input_b)
        elif 'INCR' in opcode:
            result = self.read_f_memory(literal, state) + 1
            store = 'f'
        elif 'DECR' in opcode:
            result = self.read_f_memory(literal, state) - 1
            store = 'f'
        elif 'ROL' in opcode:
            result = self.read_f_memory(literal, state) << 1
            store = 'f'
        elif 'ROR' in opcode:
            result = self.read_f_memory(literal, state) >> 1
            store = 'f'
        elif 'NAND' in opcode:
            result = ~ (input_a & input_b)
        elif 'NOR' in opcode:
            result = ~ (input_a | input_b)
        elif 'XOR' in opcode:
            result = input_a ^ input_b
        else:
            raise Exception("Unknown alu operation.")

        self.store_at_location(store, literal, result, state)
        state.program_counter += 1

    def get_load_and_store_location(self, opcode):
        if ',' in opcode:
            opcode_split = opcode.split(',')
            store = opcode_split[-1]
            load = 'f'
        else:
            store = 'w'
            load = 'l'

        return store, load

    def load_from_location(self, location, literal, state):
        if location == 'f':
            value = self.read_f_memory(literal, state)
        else:
            value = literal

        return value

    def store_at_location(self, location, address, value, state):
        if location == 'f':
            self.write_f_memory(address, value, state)
        else:
            state.w_register = value

    def read_f_memory(self, address, state: MicrocontrollerState):
        return state.f_memory[address + state.variable_scope_stack[-1]]

    def write_f_memory(self, address, value, state: MicrocontrollerState):
        state.f_memory[address + state.variable_scope_stack[-1]] = value
