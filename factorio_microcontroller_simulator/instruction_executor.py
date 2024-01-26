import re

from factorio_microcontroller_simulator.igpu_instruction_executor import IGPUInstructionExecutor
from factorio_microcontroller_simulator.microcontroller_state import MicrocontrollerState

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

IGPU_OPERATIONS = [
    "IGRENDER", "IGDRAWPL", "IGDRAWPF", "IGCLEAR", "IGDRAWVL",
    "IGDRAWVF", "IGDRAWHL", "IGDRAWHF", "IGDRAWRL", "IGDRAWRF",
    "IGSETFL", "IGSETFF", "IGSAVE", "IGLOAD"
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

        elif 'RIN' in opcode:
            self.execute_input_operation(opcode, literal, state)

        elif any(igpu_op in opcode for igpu_op in IGPU_OPERATIONS):
            IGPUInstructionExecutor.execute_operation(opcode, literal, state)

        else:
            raise Exception("Unknown instruction: " + opcode)

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
        elif load == 'W':
            state.output_registers[output_index] = state.w_register
        else:
            state.output_registers[output_index] = state.read_f_memory(literal)

        state.program_counter += 1

    def execute_input_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        opcode_split = opcode.split(',')
        input_index = int(opcode_split[1]) - 1
        store = opcode_split[0][-1]
        address = literal
        value = state.input_values[input_index]

        self.store_at_location(store, address, value, state)
        state.program_counter += 1

    def execute_branching_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        if any(conditional_op in opcode for conditional_op in ["GRT", "LESS", "EQ"]):
            input_a = state.w_register

            opcode_split = re.split(r'(\d+)', opcode)
            if opcode_split[0][-1] == 'F':
                input_b = state.read_f_memory(literal)
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
                state.w_register = state.read_f_memory(literal)
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
            store = 'W'
            address = 0
            value = literal
        elif opcode == 'MOVWF':
            store = 'F'
            address = literal
            value = state.w_register
        elif opcode == 'MOVFW':
            store = 'W'
            address = literal
            value = state.read_f_memory(address)
        elif opcode == 'MOVLF':
            store = 'F'
            address = state.w_register
            value = literal
        else:
            raise Exception("Unknown memory operation.")

        self.store_at_location(store, address, value, state)
        state.program_counter += 1

    def execute_alu_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        store, load = self.get_alu_load_and_store_location(opcode)

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
            result = state.read_f_memory(literal) + 1
            store = 'F'
        elif 'DECR' in opcode:
            result = state.read_f_memory(literal) - 1
            store = 'F'
        elif 'ROL' in opcode:
            result = state.read_f_memory(literal) << 1
            store = 'F'
        elif 'ROR' in opcode:
            result = state.read_f_memory(literal) >> 1
            store = 'F'
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

    def get_alu_load_and_store_location(self, opcode):
        if ',' in opcode:
            opcode_split = opcode.split(',')
            store = opcode_split[-1]
            load = 'F'
        else:
            store = 'W'
            load = 'L'

        return store, load

    def load_from_location(self, location, literal, state):
        if location.upper() == 'F':
            value = state.read_f_memory(literal)
        elif location.upper() == 'L':
            value = literal
        else:
            raise Exception("Invalid load location: " + location)

        return value

    def store_at_location(self, location, address, value, state):
        if location.upper() == 'F':
            state.write_f_memory(address, value)
        elif location.upper() == 'W':
            state.w_register = value
        else:
            raise Exception("Invalid store location: " + location)
