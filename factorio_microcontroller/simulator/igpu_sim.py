from pathlib import Path

from simulator.constants import SCREEN_SIZE
from simulator.igpu_state import IGPUState
from PIL import Image
import imageio

IMAGES_FOLDER = Path(__file__).parent / "screen_images"


class IGPUSim:
    def __init__(self):
        self.igpu_states: list[IGPUState] = []

    def add_state(self, state: IGPUState):
        self.igpu_states.append(state)

    def run(self):
        total_states = len(self.igpu_states)
        print("\nCreating gif ...")
        size = 4

        with imageio.get_writer("screen.gif", mode='I', duration=10) as writer:
            for i, state in enumerate(self.igpu_states):
                # TODO make a input arg?
                if i % 10 != 0 and i != len(self.igpu_states) - 1:
                    continue

                if i % 1000 == 0:
                    print("Processed: " + str(i) + "/" + str(total_states))
                image = self.get_image_from_buffer(state.screen_buffer)
                writer.append_data(image.convert('P').resize((size*SCREEN_SIZE, size*32)))

        image = self.get_image_from_buffer(state.screen_buffer)
        image.save(IMAGES_FOLDER / "screen_end.png")

        print("Done")

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
