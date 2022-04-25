from dataclasses import dataclass


@dataclass()
class MicrocontrollerState:
    w_register: int
    f_memory: dict[int]


ALU_OPERATIONS = [
    "ADD", "SUB", "MUL", "DIV",
    "MOD", "INCR", "DECR",
    "ROL", "ROR",
    "NAND", "NOR", "XOR",
]


class InstructionExecutor:
    def execute(self, opcode: str, literal: int, state: MicrocontrollerState):
        if any(alu_op in opcode for alu_op in ALU_OPERATIONS):
            self.execute_alu_operation(opcode, literal, state)
        elif 'MOV' in opcode:
            self.execute_memory_operation(opcode, literal, state)

    def execute_memory_operation(self, opcode: str, literal: int, state: MicrocontrollerState):
        if opcode == 'MOVLW':
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
            value = state.f_memory[address]
        elif opcode == 'MOVLF':
            store = 'f'
            address = state.w_register
            value = literal
        else:
            raise Exception("Unknown memory operation.")

        self.store_at_location(store, address, value, state)

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
            result = state.f_memory[literal] + 1
            store = 'f'
        elif 'DECR' in opcode:
            result = state.f_memory[literal] - 1
            store = 'f'
        elif 'ROL' in opcode:
            result = state.f_memory[literal] << 1
            store = 'f'
        elif 'ROR' in opcode:
            result = state.f_memory[literal] >> 1
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
            if literal in state.f_memory:
                value = state.f_memory[literal]
            else:
                value = 0
                print("Warning: uninitialized memory read")
        else:
            value = literal

        return value

    def store_at_location(self, location, address, value, state):
        if location == 'f':
            state.f_memory[address] = value
        else:
            state.w_register = value
