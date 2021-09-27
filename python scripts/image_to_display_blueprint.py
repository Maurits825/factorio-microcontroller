import math
import zlib
import json
import copy
from base64 import b64decode, b64encode
import click
import pyperclip
from PIL import Image
import numpy as np

max_signal_per_comb = 20


class Img2Bp:
    def __init__(self):
        blueprint_string = self.load_blueprint_strings()
        self.display_tileable = blueprint_string['display_tileable']
        self.lamp_bp = blueprint_string['lamp']
        self.constant_comb_blueprint = blueprint_string['constant_combinator']

    def load_blueprint_strings(self):
        json_file = '../resources/blueprint_strings.json'
        with open(json_file) as f:
            blueprint_json = json.load(f)
        return blueprint_json

    def decode_blueprint(self, blueprint_string):
        raw_json = zlib.decompress(b64decode(blueprint_string.encode('ascii')[1:]))
        return json.loads(raw_json)

    def encode_dict(self, blueprint_dict):
        data = json.dumps(blueprint_dict).encode('utf-8')
        return '0' + b64encode(zlib.compress(data)).decode('ascii')

    def create_display_bp(self, width, height):
        #TODO this uses a blueprint of a array of light already wired, so this doesnt work
        display_json = self.decode_blueprint('')
        lamp_json = self.decode_blueprint(self.lamp_bp)
        signal_map = self.load_signal_map()
        lamp_control_behavior_template = lamp_json['blueprint']['entities'][1]['control_behavior']

        top_left_x = display_json['blueprint']['entities'][1]['position']['x']
        top_left_y = display_json['blueprint']['entities'][1]['position']['y']

        for entity in display_json['blueprint']['entities']:
            x = entity['position']['x'] - top_left_x
            y = entity['position']['y'] - top_left_y
            linear_index = int((x % width) + (y * height))
            entity['control_behavior'] = copy.deepcopy(lamp_control_behavior_template)
            entity['control_behavior']['circuit_condition']['first_signal'] = signal_map[linear_index]

        return self.encode_dict(display_json)

    def load_signal_map(self):
        json_file = "../resources/signal_map.json"
        with open(json_file) as f:
            signal_map = json.load(f)
        return signal_map

    def load_binary_image(self, image_name, x, y):
        image_raw = Image.open(image_name).convert('L')
        image_resize = image_raw.resize((x, y))
        np_img = np.array(image_resize)
        np_img = np.where(np_img > 128, 255, 0)
        return np_img

    # this just make the rom, not the display
    def convert_image_to_rom_bp(self, image_name, width, height):
        np_img_flat = self.load_binary_image(image_name, width, height).flatten()
        rom_blueprint_template = self.decode_blueprint(self.constant_comb_blueprint)
        constant_comb_entity_template = copy.deepcopy(rom_blueprint_template['blueprint']['entities'][0])
        signal_template = copy.deepcopy(constant_comb_entity_template['control_behavior']['filters'][0])
        rom_blueprint_template['blueprint']['entities'].clear()
        signal_map = self.load_signal_map()

        constant_comb_idx = -1
        signal_comb_idx = max_signal_per_comb + 1
        rom_blueprint = copy.deepcopy(rom_blueprint_template)

        for index, value in enumerate(np_img_flat):
            if value == 0:
                if signal_comb_idx > max_signal_per_comb:
                    rom_blueprint['blueprint']['entities'].append(copy.deepcopy(constant_comb_entity_template))

                    signal_comb_idx = 1
                    constant_comb_idx += 1

                    rom_blueprint['blueprint']['entities'][constant_comb_idx]['position'] = {'x': 0,
                                                                                             'y': constant_comb_idx}
                    rom_blueprint['blueprint']['entities'][constant_comb_idx]['entity_number'] = constant_comb_idx + 1

                signal = copy.deepcopy(signal_template)
                signal['signal']['type'] = signal_map[index]['type']
                signal['signal']['name'] = signal_map[index]['name']
                signal['count'] = 1
                signal['index'] = signal_comb_idx
                rom_blueprint['blueprint']['entities'][constant_comb_idx]['control_behavior']['filters'].append(signal)

                signal_comb_idx += 1

        comb_count = len(rom_blueprint['blueprint']['entities'])
        for idx, combinator in enumerate(rom_blueprint['blueprint']['entities']):
            if idx == 0:
                combinator['connections'] = {'1': {'red': [{'entity_id': 2}]}}
            elif idx == comb_count - 1:
                combinator['connections'] = {'1': {'red': [{'entity_id': idx}]}}
            else:
                combinator['connections'] = {'1': {'red': [{'entity_id': idx}, {'entity_id': idx + 2}]}}

        return self.encode_dict(rom_blueprint)

    def convert_image_using_tilable(self, image_name, size_x, size_y):
        np_img = self.load_binary_image(image_name, 18 * size_x, 18 * size_y)
        Image.fromarray(np_img).show()

        rom_blueprint_template = self.decode_blueprint(self.constant_comb_blueprint)
        constant_comb_entity_template = copy.deepcopy(rom_blueprint_template['blueprint']['entities'][0])
        signal_template = copy.deepcopy(constant_comb_entity_template['control_behavior']['filters'][0])
        rom_blueprint_template['blueprint']['entities'].clear()

        signal_map = self.load_signal_map()

        display_template = self.decode_blueprint(self.display_tileable)

        display_entities_size = len(display_template['blueprint']['entities']) + 1
        # allocate entity numbers for the constant combinators
        display_entities_total_size = display_entities_size + 4*4

        display_bp_final = copy.deepcopy(display_template)
        display_bp_final['blueprint']['entities'].clear()

        dead_pixel_map = dict()
        dead_pixel_map[0] = 80
        dead_pixel_map[1] = 72
        dead_pixel_map[2] = 8
        dead_pixel_map[3] = 0

        substation_base_index = 142
        substation_base_entity_id = 145

        # iterate over every tile
        for tile_x in range(size_x):
            for tile_y in range(size_y):
                display_tile = copy.deepcopy(display_template['blueprint']['entities'])

                section_combinators_template = dict()
                section_combinators_template[3] = display_tile.pop(270)
                section_combinators_template[2] = display_tile.pop(163)
                section_combinators_template[1] = display_tile.pop(91)
                section_combinators_template[0] = display_tile.pop(0)

                # iterate over the sections in the tile
                #TODO can make the tile 2 sections of 9*18=160 signals, will need to add virtual signals to signal map
                for section in range(4):
                    constant_comb_idx = -1
                    signal_comb_idx = max_signal_per_comb + 1
                    current_section_combinators = []

                    # check if the pixel should be on
                    for pixel in range(81):  # 81 pixels per section (actual is 80 because of substation)
                        if pixel == dead_pixel_map[section]:
                            continue
                        index_x = int((tile_x * 18) + (pixel % 9) + (9 * (section % 2)))
                        index_y = int((tile_y * 18) + (math.floor(pixel / 9)) + (9 * (math.floor(section / 2))))
                        img_value = np_img[index_y][index_x]  # switch x and y because np

                        if img_value == 0:
                            if signal_comb_idx > max_signal_per_comb:
                                current_section_combinators.append(copy.deepcopy(section_combinators_template[section]))

                                signal_comb_idx = 1
                                constant_comb_idx += 1

                                current_section_combinators[constant_comb_idx]['position']['y'] += constant_comb_idx
                                current_section_combinators[constant_comb_idx]['entity_number'] = display_entities_size + constant_comb_idx + 4*section
                                current_section_combinators[constant_comb_idx]['control_behavior'] = {'filters': []}

                            signal = copy.deepcopy(signal_template)
                            signal['signal']['type'] = signal_map[pixel]['type']
                            signal['signal']['name'] = signal_map[pixel]['name']
                            signal['count'] = 1
                            signal['index'] = signal_comb_idx
                            current_section_combinators[constant_comb_idx]['control_behavior']['filters'].append(signal)

                            signal_comb_idx += 1
                    # section rom is done, do the wiring
                    comb_count = len(current_section_combinators)
                    entity_id_offset = display_entities_size + 4*section
                    for idx, combinator in enumerate(current_section_combinators):
                        if idx == 0:
                            combinator['connections']['1']['red'].append({'entity_id': 1 + entity_id_offset})
                        elif idx == comb_count - 1:
                            combinator['connections'] = {'1': {'red': [{'entity_id': idx - 1 + entity_id_offset}]}}
                        else:
                            combinator['connections'] = {'1': {'red': [{'entity_id': idx + entity_id_offset}, {'entity_id': idx + 2 +entity_id_offset}]}}

                    # add the rom to the tile
                    display_tile += current_section_combinators

                # fix all positions and entity id based on tile after finishing the 4 sections
                entity_id_increment = display_entities_total_size * size_x * tile_y + display_entities_total_size * tile_x
                for entity in display_tile:
                    entity['position']['x'] += (tile_x * 19)
                    entity['position']['y'] += (tile_y * 18)
                    entity['entity_number'] += entity_id_increment
                    if 'connections' in entity:
                        for _, connection in entity['connections'].items():
                            for __, color in connection.items():
                                for number in color:
                                    number['entity_id'] += entity_id_increment

                # add substation wiring
                if tile_y > 0:
                    entity_id = substation_base_entity_id + (display_entities_total_size * tile_x) + (display_entities_total_size * (tile_y-1) * size_x)
                    display_tile[substation_base_index]['neighbours'] = [entity_id]

                # append the display tile entities to the final blueprint
                display_bp_final['blueprint']['entities'] += display_tile

        return self.encode_dict(display_bp_final)


@click.command()
@click.option('--img', '-i', help='Name of the image file')
@click.option('--width', '-w', help='Width of the blueprint', default=10)
@click.option('--height', '-h', help='Length of the blueprint',  default=10)
@click.option('--clipboard', '-c', help='Copy blueprint to the clipboard', is_flag=True)
def main(img, width, height, clipboard):
    img_2_bp = Img2Bp()
    if img:
        blueprint = img_2_bp.convert_image_using_tilable(img, width, height)
        if clipboard:
            pyperclip.copy(blueprint)
            print('Image blueprint copied to clipboard')
        else:
            print(blueprint)
    else:
        print("Incorrect input args, see --help")


if __name__ == '__main__':
    main()
