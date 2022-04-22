import math
import zlib
import json
import copy
from base64 import b64decode, b64encode
import click
import pyperclip
from PIL import Image
import numpy as np
from PIL import Image, ImageSequence


max_signal_per_comb = 20


class Img2Bp:
    def __init__(self):
        blueprint_string = self.load_blueprint_strings()
        self.display_tileable = blueprint_string['display_tileable']
        self.lamp_bp = blueprint_string['lamp']
        self.constant_comb_blueprint = blueprint_string['constant_combinator']
        self.lcd_rom = blueprint_string['lcd_rom']

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

    def create_custom_bp(self):
        bp = '0eNq9mm2O2yAQQO/Cb7MKY5w4kXqSahVhPElQbexivGq0ygF6i56tJylO2tUuKqpQNf4Tidh8PY2HB/Yra7oZR2esZ4dXZvRgJ3b4/Momc7aqW/7z1xHZgRmPPSuYVf1SmnrVdbxT/chuBTO2xW/sIG7PBUPrjTf4aOVeuB7t3Dfowg1/q1+wcZhClcEuvYVmeF0/VQW7sgPsn6rQfBiUd0N3bPCiXszglvu0cXo2/hiutW+VT8ZN/viPoav2RVmNLf/dBHv0MHm1MBBLoR+VU37piH1aLs8Tho66wYVZeTfjo4ZFvXQ8LT2J5cdh+37WJpTgVnwoy9vz7fbuvz9kIJdMTUFG67mfu/vMKaGIBIQyE0IpKCA4b7oO3ZX72TmkDQ8Zhcc2QUbmktmQkDH+0qM3mgcGjbErBMpHPGUCT5WLp6TAM03YN52xZ94rfTEWOZDS2UZ06gSdbS4dWIeOIKVTRnSqBJ1dLp2KgE6jvA8phxRIHQERmwSROpeIXCdeSlI8VYRnl6Czz6Wzo4sX3n8Bjl9nM/ZhlLSpeBOHDyQAiU0uoS0hoXXo7CI4+xSbXAMuKQy4wc5z0/ezDWNbK35iExYpFRa5LlzWJIxUqESKZB8TSXmxyBVjSSHGzWCCFtMGSezDIiXEIteIJYURN+bMsQsTc8GJx6FDWjqxDouUD4tcIZYUQtzMzqLjvbHLKt66sK2i5RMLsUgZschVYgl0fIyd0HnqJyvWYZHyYZErxJJCiPUFe6NVx8dOUa9MsRhDSoxFrhlLCjPWYVTOnOYzcbaJhVikjFjkKrGkUOJQQzv0tFAgtmBIWTDkWrDckkBRxDk3Nl+RUl/IVV+5p4mSKczwPjHuhmYgPv6NrReSB8C51itrKjwBxGoHfLEDQ8qBIdeBK0HCZxzDkj044jQTezCkPBhyPbja0GHRqiFWYIgVGFIKDLkKXFEosHZzizxsnHijnEPaXAyx/0LKfyHXfyugi5pgeNSrdiy/kJJfyJXfikJ+WzPpi3Jn5C2eMGwPVjqjgdiEy5QJQ64JVxQm3KI27ZJ31lmsIDZiSBkx5BpxRWHEbycTp7DRVJr2GStjMy5TZlzmmnG1pYSD9ry8XFjOQmmjJzZlSJlymWvK1Z4M0GCXt71/+1BiE+H5+f3Hf0ZQMmBy1biqKQNmtfMsiOW4fMjxc/EY2uHdtzsFe0E33ecDtZC7PexkuZX7kNJvvwCF7U9e'
        lamps = self.decode_blueprint(bp)
        signal_map = self.load_signal_map()

        for count, entity in enumerate(lamps['blueprint']['entities']):
            entity['control_behavior']['circuit_condition']['constant'] = 0
            entity['control_behavior']['circuit_condition']['comparator'] = '≠'

        print(self.encode_dict(lamps))

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

    def load_signal_map(self): #TODO make this a class var?
        json_file = "../resources/signal_map.json"
        with open(json_file) as f:
            signal_map = json.load(f)
        return signal_map

    def load_binary_image(self, image_name, x, y):
        img = Image.open(image_name)
        return self.convert_image(img, x, y)

    def convert_image(self, image, x, y):
        image_resize = image.resize((x, y)).convert('L')
        #image_resize.show()
        np_img = np.array(image_resize)
        np_img = np.where(np_img > 128, 1, 0)
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
                #TODO magic numbers are total_sections=4, 2 section width = 18?, section width=9, section % 2-->remove i guess :)
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

    def create_LCD_rom_bp(self, gif_name):
        lcd_width = 36
        lcd_height = 32
        bits = 32

        #load gif
        gif = Image.open(gif_name)
        frames = np.array(
            [np.array(self.convert_image(frame.copy(), lcd_width, lcd_height))
             for frame in ImageSequence.Iterator(gif)])

        signal_map = self.load_signal_map()
        #TODO make this simpler/refactor repeated code
        rom_blueprint_template = self.decode_blueprint(self.constant_comb_blueprint)
        constant_comb_entity_template = copy.deepcopy(rom_blueprint_template['blueprint']['entities'][0])
        signal_template = copy.deepcopy(constant_comb_entity_template['control_behavior']['filters'][0])

        lcd_rom_template = self.decode_blueprint(self.lcd_rom)
        final_rom = copy.deepcopy(lcd_rom_template)
        final_rom['blueprint']['entities'].clear()

        entity_count = len(lcd_rom_template['blueprint']['entities'])

        for frame_count, frame in enumerate(frames):
            current_rom_section = copy.deepcopy(lcd_rom_template)['blueprint']['entities']
            signal_comb_idx = 1
            constant_comb_entity_id = 2
            current_constant_comb = current_rom_section[constant_comb_entity_id-1]
            current_rom_section[constant_comb_entity_id-1]['control_behavior'] = {'filters': []}
            for x in range(lcd_width):
                value_str = ''
                for binary in frame[:, x]:
                    value_str += str(binary)
                value_int = int(value_str, 2)
                if (value_int & (1 << (bits - 1))) != 0:
                    value_int = value_int - (1 << bits)
                signal = copy.deepcopy(signal_template)
                signal['signal']['type'] = signal_map[x]['type']
                signal['signal']['name'] = signal_map[x]['name']
                signal['count'] = value_int
                signal['index'] = signal_comb_idx

                current_constant_comb['control_behavior']['filters'].append(signal)
                signal_comb_idx += 1

                if signal_comb_idx > max_signal_per_comb:
                    signal_comb_idx = 1
                    constant_comb_entity_id += 1
                    current_constant_comb = current_rom_section[constant_comb_entity_id-1]
                    current_rom_section[constant_comb_entity_id-1]['control_behavior'] = {'filters': []}

            # fix id and pos
            # TODO make function?
            entity_id_increment = frame_count * entity_count
            for entity in current_rom_section:
                entity['position']['x'] += frame_count
                entity['entity_number'] += entity_id_increment
                if 'connections' in entity:
                    for _, connection in entity['connections'].items():
                        for __, color in connection.items():
                            for number in color:
                                number['entity_id'] += entity_id_increment

            # add wiring
            if frame_count > 0:
                current_rom_section[0]['connections']['1']['green'] = [{'entity_id': current_rom_section[0]['entity_number'] - entity_count, 'circuit_id': 1}]
                current_rom_section[0]['connections']['2'] = {'red': [{'entity_id': current_rom_section[0]['entity_number'] - entity_count, 'circuit_id': 2}]}

            # add frame_count number
            current_rom_section[0]['control_behavior']['decider_conditions']['constant'] = frame_count + 1

            # add current rom section
            final_rom['blueprint']['entities'] += current_rom_section
            # skip over next comb
            constant_comb_entity_id += 1

        return self.encode_dict(final_rom)


@click.command()
@click.option('--img', '-i', help='Name of the image file')
@click.option('--gif', '-f', help='Name of the gif file')
@click.option('--width', '-w', help='Width of the image blueprint', default=10)
@click.option('--height', '-h', help='Height of the image blueprint',  default=10)
@click.option('--clipboard', '-c', help='Copy blueprint to the clipboard', is_flag=True)
def main(img, gif, width, height, clipboard):
    img_2_bp = Img2Bp()
    #img_2_bp.create_custom_bp()

    blueprint = ''
    if img:
        blueprint = img_2_bp.convert_image_using_tilable(img, width, height)
    elif gif:
        blueprint = img_2_bp.create_LCD_rom_bp(gif)
    else:
        print("Incorrect input args, see --help")
        exit()

    if clipboard:
        pyperclip.copy(blueprint)
        print('Blueprint copied to clipboard')
    else:
        print(blueprint)


if __name__ == '__main__':
    main()
