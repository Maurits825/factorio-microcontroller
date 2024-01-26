from pathlib import Path

import numpy as np

from factorio_microcontroller_simulator.constants import SCREEN_SIZE
from factorio_microcontroller_simulator.igpu_state import IGPUState
from PIL import Image
import imageio

IMAGES_FOLDER = Path(__file__).parent / "screen_images"


class IGPUSim:
    def __init__(self):
        self.igpu_states: list[IGPUState] = []

    def add_state(self, state: IGPUState):
        self.igpu_states.append(state)

    def run(self):
        with imageio.get_writer("screen.gif", mode='I', duration=50) as writer:
            for i, state in enumerate(self.igpu_states):
                image = self.get_image_from_buffer(state.screen_buffer)
                #image.save(IMAGES_FOLDER / ("screen_" + str(i) + ".png"))
                writer.append_data(image.convert('P'))

    def get_binary_array_from_buffer(self, buffer):
        binary_array = [[0 for _ in range(SCREEN_SIZE)] for _ in range(32)]
        for x, value in enumerate(buffer):
            binary_string = bin(value)[:1:-1]
            for y, bit in enumerate(binary_string):
                binary_array[y][x] = int(bit)
        return binary_array

    def get_image_from_buffer(self, buffer):
        binary_array = self.get_binary_array_from_buffer(buffer)

        image = Image.new("1", (SCREEN_SIZE, 32))
        pixels = [1 if pixel == 1 else 0 for row in binary_array[::-1] for pixel in row]

        image.putdata(pixels)
        return image
