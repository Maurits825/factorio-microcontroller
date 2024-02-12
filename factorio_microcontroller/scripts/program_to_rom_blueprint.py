import zlib
import json
import copy
from base64 import b64decode, b64encode
from pathlib import Path

import click
import pyperclip

RESOURCE_FOLDER = Path(__file__).parent.parent.parent / "resources"

MAX_CONSTANT_COMB_SIGNALS = 20
BITS = 32


class Program2ROM:
    def __init__(self):
        self.blueprint_strings = self.load_json(RESOURCE_FOLDER / "blueprint_strings.json")
        self.signal_map = self.load_json(RESOURCE_FOLDER / "signal_map.json")
        self.signal_map_max = len(self.signal_map)

        constant_comb_blueprint = self.blueprint_strings['constant_combinator']

        self.rom_blueprint_template = self.decode_blueprint(constant_comb_blueprint)
        self.constant_comb_entity_template = copy.deepcopy(self.rom_blueprint_template['blueprint']['entities'][0])
        self.signal_template = copy.deepcopy(self.constant_comb_entity_template['control_behavior']['filters'][0])

        self.rom_blueprint_template['blueprint']['entities'].clear()
        self.constant_comb_entity_template['control_behavior']['filters'].clear()

    def load_json(self, json_file):
        with open(json_file) as f:
            json_dict = json.load(f)
        return json_dict

    def convert_file_to_base10_list(self, file_name):
        program = []
        with open(file_name) as file:
            for line in file:
                decimal_value = int(line, 2)
                if (decimal_value & (1 << (BITS - 1))) != 0:
                    decimal_value = decimal_value - (1 << BITS)
                program.append(decimal_value)

        return program

    def decode_blueprint(self, blueprint_string):
        raw_json = zlib.decompress(b64decode(blueprint_string.encode('ascii')[1:]))
        return json.loads(raw_json)

    def encode_dict(self, blueprint_dict):
        data = json.dumps(blueprint_dict).encode('utf-8')
        return '0' + b64encode(zlib.compress(data)).decode('ascii')

    def get_rom_blueprint(self, decimal_program) -> str:
        program_split = [decimal_program[i:i + self.signal_map_max]
                         for i in range(0, len(decimal_program), self.signal_map_max)]

        rom_blueprint = self.decode_blueprint(self.blueprint_strings["rom_template"])
        rom_blueprint["blueprint"]["entities"].clear()

        for i, decimal_lines in enumerate(program_split):
            rom_entities = self.get_rom_entities(decimal_lines)
            self.update_entities(rom_entities, i)
            rom_blueprint["blueprint"]["entities"] += rom_entities

        return self.encode_dict(rom_blueprint)

    def update_entities(self, entities, offset):
        id_offset = offset * len(entities)
        for entity in entities:
            entity["position"]["x"] -= offset
            entity["entity_number"] += id_offset

            for _, connection in entity["connections"].items():
                for __, color in connection.items():
                    for number in color:
                        number["entity_id"] += id_offset

    def get_rom_entities(self, decimal_lines) -> list:
        rom_map_entities = self.decode_blueprint(self.blueprint_strings["rom_template"])["blueprint"]["entities"]
        for entity in rom_map_entities[:-1]:
            entity['control_behavior']['filters'].clear()

        for i, line in enumerate(decimal_lines):
            signal = copy.deepcopy(self.signal_template)
            signal['signal']['type'] = self.signal_map[i]['type']
            signal['signal']['name'] = self.signal_map[i]['name']
            signal['count'] = line
            signal['index'] = (i % MAX_CONSTANT_COMB_SIGNALS) + 1
            rom_map_entities[i // MAX_CONSTANT_COMB_SIGNALS]['control_behavior']['filters'].append(signal)

        return rom_map_entities

    def create_rom_map_blueprint(self):
        constant_comb_idx = -1
        signal_comb_idx = MAX_CONSTANT_COMB_SIGNALS + 1
        rom_map = copy.deepcopy(self.rom_blueprint_template)
        rom_map['blueprint']['label'] = 'Rom Map'
        for signal_map_idx, signal in enumerate(self.signal_map):
            if signal_comb_idx > MAX_CONSTANT_COMB_SIGNALS:
                rom_map['blueprint']['entities'].append(copy.deepcopy(self.constant_comb_entity_template))

                signal_comb_idx = 1
                constant_comb_idx += 1

                rom_map['blueprint']['entities'][constant_comb_idx]['position'] = {'x': 0, 'y': constant_comb_idx}

            signal_copy = copy.deepcopy(self.signal_template)
            signal_copy['signal']['type'] = signal['type']
            signal_copy['signal']['name'] = signal['name']
            signal_copy['count'] = signal_map_idx + 1
            signal_copy['index'] = signal_comb_idx
            rom_map['blueprint']['entities'][constant_comb_idx]['control_behavior']['filters'].append(signal_copy)

            signal_comb_idx += 1

        return self.encode_dict(rom_map)


@click.command()
@click.option('--bin_file', '-b', help='Name of file containing the program in binary')
@click.option('--rom_map', '-m', help='Generate the rom map blueprint', is_flag=True)
@click.option('--clipboard', '-c', help='Copy blueprint to the clipboard', is_flag=True)
def main(bin_file, rom_map, clipboard):
    binary2rom = Program2ROM()
    if rom_map:
        rom_map_blueprint = binary2rom.create_rom_map_blueprint()
        if clipboard:
            pyperclip.copy(rom_map_blueprint)
            print('ROM map blueprint copied to clipboard')
        else:
            print(rom_map_blueprint)
    elif bin_file:
        program = binary2rom.convert_file_to_base10_list(bin_file)
        program_rom_blueprint = binary2rom.get_rom_blueprint(program)
        if clipboard:
            pyperclip.copy(program_rom_blueprint)
            print('Program blueprint copied to clipboard')
        else:
            print(program_rom_blueprint)
    else:
        print("Incorrect input args, see --help")


if __name__ == '__main__':
    main()
