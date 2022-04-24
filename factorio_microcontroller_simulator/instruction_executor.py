from dataclasses import dataclass


@dataclass()
class MicrocontrollerState:
    w_register: int
    f_memory: dict[int]


class InstructionExecutor:
    def __init__(self):
        pass

    def execute(self, opcode: str, literal: int, state: MicrocontrollerState):
        #just a huge if statement?
        if 'ADD' in opcode:
            store, load = self.get_load_and_store_location(opcode)

            input_a = state.w_register
            input_b = self.load_from_location(load, literal, state)

            result = input_a + input_b
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

    def store_at_location(self, location, literal, value, state):
        if location == 'f':
            state.f_memory[literal] = value
        else:
            state.w_register = value
