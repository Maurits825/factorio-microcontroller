from dataclasses import dataclass

from simulator.constants import SCREEN_SIZE


@dataclass()
class IGPUState:
    buffer1: list
    buffer2: list
    screen_buffer: list
    status_flag: int

    def __init__(self):
        self.buffer1 = [0 for _ in range(SCREEN_SIZE)]
        self.buffer2 = [0 for _ in range(SCREEN_SIZE)]
        self.screen_buffer = [0 for _ in range(SCREEN_SIZE)]
        self.status_flag = 0
