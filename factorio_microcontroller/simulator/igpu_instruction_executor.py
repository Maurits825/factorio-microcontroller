from dataclasses import dataclass

from factorio_microcontroller_simulator.constants import SCREEN_SIZE
from factorio_microcontroller_simulator.microcontroller_state import MicrocontrollerState


@dataclass()
class InputArgs:
    x: int
    y: int
    a: int
    b: int


class IGPUInstructionExecutor:
    @staticmethod
    def execute_operation(opcode: str, literal: int, state: MicrocontrollerState):
        active_buffer = state.igpu_state.buffer1 if state.igpu_state.status_flag % 2 == 0 else state.igpu_state.buffer2
        input_value = state.read_f_memory(literal) if opcode[-1] == 'F' else literal
        input_args = IGPUInstructionExecutor.get_input_args(input_value)

        if 'IGRENDER' in opcode:
            state.igpu_state.screen_buffer = [
                state.igpu_state.buffer1[i] | state.igpu_state.buffer2[i] for i in range(SCREEN_SIZE)
            ]
        elif 'IGCLEAR' in opcode:
            for i in range(SCREEN_SIZE):
                active_buffer[i] = 0
        elif 'IGSETF' in opcode:
            state.igpu_state.status_flag = input_value  # TODO later have to fix if multiple flags
        elif 'IGDRAWP' in opcode:
            active_buffer[input_args.x] = active_buffer[input_args.x] | (1 << input_args.y)
        elif 'IGDRAWR' in opcode:
            for x in range(input_args.x, input_args.a):  # TODO +1 here because range stop is exclusive?
                active_buffer[x] = active_buffer[x] | ((1 << (input_args.b + 1)) - (1 << input_args.y))
        elif 'IGDRAWH' in opcode:
            for x in range(input_args.x, input_args.x + input_args.b):
                active_buffer[x] = active_buffer[x] | (1 << input_args.y)
        else:
            raise Exception("Unknown igpu operation: " + opcode)

        state.program_counter += 1

    @staticmethod
    def get_input_args(literal):
        return InputArgs(
            x=(literal >> 6) % 64,
            y=(literal >> 0) % 64,
            a=(literal >> 18) % 64,
            b=(literal >> 12) % 64,
        )
