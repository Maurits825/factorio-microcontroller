import zlib
import json
import copy
from base64 import b64decode, b64encode

constant_comb_blueprint = "0eNp9UEuKwzAMvYvWTiFO0493PUcZipNqWkEiB0cJE4LvXrmBoZuZnSSe3m+FpptwiMQCbgVqA4/griuM9GDf5ZssA4IDEuzBAPs+bxknnqVoQ98QewkRkgHiO/6AK9OXAWQhIdzo3sty46lvMCrgXyIDQxj1N3DWV77C1rvawKJTZXe1Ct0pYrshrMkkEkN3a/DpZ1IGffumTjD+EWamKJNefm1siOKSQ7Rhym2Un3FSTvSuwH00ZmBWic3Fqdwfz/a4t1V1qg8pvQAxenOf"
max_signal_per_comb = 20


class Binary2ROM:

    def __init__(self, program_name):
        self.rom_blueprint = self.decode_blueprint(constant_comb_blueprint)
        self.constant_comb_entity_template = self.rom_blueprint['blueprint']['entities'][0]
        self.signal_template = self.constant_comb_entity_template['control_behavior']['filters'][0]

        self.rom_blueprint['blueprint']['label'] = program_name

        self.rom_blueprint['blueprint']['entities'].clear()
        self.constant_comb_entity_template['control_behavior']['filters'].clear()

        self.signal_map = self.load_signal_map()
        self.signal_map_max =  len(self.signal_map)

    def load_signal_map(self):
        json_file = "../resources/signal_map.json"
        with open(json_file) as f:
            signal_map = json.load(f)
        return signal_map

    def decode_blueprint(self, blueprint_string):
        raw_json = zlib.decompress(b64decode(blueprint_string.encode('ascii')[1:]))
        return json.loads(raw_json)

    def encode_dict(self, blueprint_dict):
        data = json.dumps(blueprint_dict).encode('utf-8')
        return '0' + b64encode(zlib.compress(data)).decode('ascii')

    def convert_program_to_rom(self, program_base10):
        constant_comb_idx = -1
        signal_comb_idx = max_signal_per_comb + 1
        signal_map_idx = 0
        for line, instruction in enumerate(program_base10):
            if signal_comb_idx > max_signal_per_comb:
                self.rom_blueprint['blueprint']['entities'].append(copy.deepcopy(self.constant_comb_entity_template))

                signal_comb_idx = 1
                constant_comb_idx += 1

                self.rom_blueprint['blueprint']['entities'][constant_comb_idx]['position'] = {'x': 0, 'y': constant_comb_idx}

            signal = copy.deepcopy(self.signal_template)
            signal['signal']['type'] = self.signal_map[signal_map_idx]['type']
            signal['signal']['name'] = self.signal_map[signal_map_idx]['name']
            signal['count'] = instruction + 1
            signal['index'] = signal_comb_idx
            self.rom_blueprint['blueprint']['entities'][constant_comb_idx]['control_behavior']['filters'].append(signal)

            signal_comb_idx += 1
            signal_map_idx += 1

        return self.encode_dict(self.rom_blueprint)

    def create_rom_map_blueprint(self):
        constant_comb_idx = -1
        signal_comb_idx = max_signal_per_comb + 1
        rom_map = copy.deepcopy(self.rom_blueprint)
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


#TODO use click to turn this into cmd line args
if __name__ == '__main__':
    binary2rom = Binary2ROM('Test')

    #also works? TODO test with 20+ lines
    rom_blueprint = binary2rom.convert_program_to_rom([101, 405])
    print(rom_blueprint)

    #this works
    #rom_map_blueprint = binary2rom.create_rom_map_blueprint()

    a=3


