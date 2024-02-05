import zlib
import json
import copy
from base64 import b64decode, b64encode
import click
import pyperclip

max_signal_per_comb = 20
bits = 32


class Program2ROM:
    def __init__(self):
        blueprint_string = self.load_blueprint_strings()
        constant_comb_blueprint = blueprint_string['constant_combinator']

        self.rom_blueprint_template = self.decode_blueprint(constant_comb_blueprint)
        self.constant_comb_entity_template = copy.deepcopy(self.rom_blueprint_template['blueprint']['entities'][0])
        self.signal_template = copy.deepcopy(self.constant_comb_entity_template['control_behavior']['filters'][0])

        self.rom_blueprint_template['blueprint']['entities'].clear()
        self.constant_comb_entity_template['control_behavior']['filters'].clear()

        self.signal_map = self.load_signal_map()
        self.signal_map_max = len(self.signal_map)

    def load_blueprint_strings(self):
        json_file = '../resources/blueprint_strings.json'
        with open(json_file) as f:
            blueprint_json = json.load(f)
        return blueprint_json

    def load_signal_map(self):
        json_file = "../resources/signal_map.json"
        with open(json_file) as f:
            signal_map = json.load(f)
        return signal_map

    def convert_file_to_base10_list(self, file_name):
        program = []
        with open(file_name) as file:
            for line in file:
                decimal_value = int(line, 2)
                if (decimal_value & (1 << (bits - 1))) != 0:
                    decimal_value = decimal_value - (1 << bits)
                program.append(decimal_value)

        return program

    def decode_blueprint(self, blueprint_string):
        raw_json = zlib.decompress(b64decode(blueprint_string.encode('ascii')[1:]))
        return json.loads(raw_json)

    def encode_dict(self, blueprint_dict):
        data = json.dumps(blueprint_dict).encode('utf-8')
        return '0' + b64encode(zlib.compress(data)).decode('ascii')

    #TODO handle program length > self.signal_map_max (137)
    def convert_program_to_rom(self, program_base10):
        #program_split = [program_base10[i:i + self.signal_map_max] for i in range(0, len(program_base10), self.signal_map_max)]

        constant_comb_idx = -1
        signal_comb_idx = max_signal_per_comb + 1
        rom_blueprint = copy.deepcopy(self.rom_blueprint_template)
        for line_num, instruction in enumerate(program_base10):
            if signal_comb_idx > max_signal_per_comb:
                rom_blueprint['blueprint']['entities'].append(copy.deepcopy(self.constant_comb_entity_template))

                signal_comb_idx = 1
                constant_comb_idx += 1

                rom_blueprint['blueprint']['entities'][constant_comb_idx]['position'] = {'x': 0, 'y': constant_comb_idx}
                rom_blueprint['blueprint']['entities'][constant_comb_idx]['entity_number'] = constant_comb_idx + 1

            signal = copy.deepcopy(self.signal_template)
            signal['signal']['type'] = self.signal_map[line_num]['type']
            signal['signal']['name'] = self.signal_map[line_num]['name']
            signal['count'] = instruction
            signal['index'] = signal_comb_idx
            rom_blueprint['blueprint']['entities'][constant_comb_idx]['control_behavior']['filters'].append(signal)

            signal_comb_idx += 1

        comb_count = len(rom_blueprint['blueprint']['entities'])
        for idx, combinator in enumerate(rom_blueprint['blueprint']['entities']):
            if idx == 0:
                combinator['connections'] = {'1': {'green': [{'entity_id': 2}]}}
            elif idx == comb_count-1:
                combinator['connections'] = {'1': {'green': [{'entity_id': idx}]}}
            else:
                combinator['connections'] = {'1': {'green': [{'entity_id': idx}, {'entity_id': idx+2}]}}

        return self.encode_dict(rom_blueprint)

    def create_rom_map_blueprint(self):
        constant_comb_idx = -1
        signal_comb_idx = max_signal_per_comb + 1
        rom_map = copy.deepcopy(self.rom_blueprint_template)
        rom_map['blueprint']['label'] = 'Rom Map'
        for signal_map_idx, signal in enumerate(self.signal_map):
            if signal_comb_idx > max_signal_per_comb:
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
        program_rom_blueprint = binary2rom.convert_program_to_rom(program)
        if clipboard:
            pyperclip.copy(program_rom_blueprint)
            print('Program blueprint copied to clipboard')
        else:
            print(program_rom_blueprint)
    else:
        print("Incorrect input args, see --help")


if __name__ == '__main__':
    main()
