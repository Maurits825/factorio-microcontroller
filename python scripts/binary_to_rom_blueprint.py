import zlib
import json
import copy
from sys import argv
from io import BytesIO
from base64 import b64decode, b64encode

constant_comb_blueprint = "0eNp9UEuKwzAMvYvWTiFO0493PUcZipNqWkEiB0cJE4LvXrmBoZuZnSSe3m+FpptwiMQCbgVqA4/griuM9GDf5ZssA4IDEuzBAPs+bxknnqVoQ98QewkRkgHiO/6AK9OXAWQhIdzo3sty46lvMCrgXyIDQxj1N3DWV77C1rvawKJTZXe1Ct0pYrshrMkkEkN3a/DpZ1IGffumTjD+EWamKJNefm1siOKSQ7Rhym2Un3FSTvSuwH00ZmBWic3Fqdwfz/a4t1V1qg8pvQAxenOf"


class Binary2ROM:

    def __init__(self, program_name):
        self.rom_blueprint = self.decode_blueprint(constant_comb_blueprint)
        self.constant_comb_entity = self.rom_blueprint['blueprint']['entities'][0]
        self.signal = self.constant_comb_entity['control_behavior']['filters'][0]

        self.rom_blueprint['blueprint']['label'] = program_name

        self.rom_blueprint['blueprint']['entities'].clear()
        self.constant_comb_entity['control_behavior']['filters'].clear()
        self.foo = 1

    def decode_blueprint(self, blueprint_string):
        raw_json = zlib.decompress(b64decode(blueprint_string.encode('ascii')[1:]))
        return json.loads(raw_json)

    def encode_dict(self, blueprint_dict):
        data = json.dumps(blueprint_dict).encode('utf-8')
        return '0' + b64encode(zlib.compress(data)).decode('ascii')


    def convert_program_to_rom(self, program_base10):
        #add an entity for every 20 signals? only hold 20 signal per constant
        self.rom_blueprint['blueprint']['entities'].append(copy.deepcopy(self.constant_comb_entity))
        #TODO when set position
        constant_comb_count = 0
        for idx, instruction in enumerate(program_base10):
            # store the value
            signal = copy.deepcopy(self.signal)
            #TODO have a json or somehting with all these signals?
            signal['signal']['type'] = 'virtual'
            signal['signal']['name'] = 'signal-B'
            signal['count'] = instruction
            signal['index'] = idx+1 # TODO this is just position? 1-20?
            self.rom_blueprint['blueprint']['entities'][constant_comb_count]['control_behavior']['filters'].append(signal)

        return self.encode_dict(self.rom_blueprint)


if __name__ == '__main__':
    binary2rom = Binary2ROM('Test')
    rom_blueprint = binary2rom.convert_program_to_rom([101, 405])
    print(rom_blueprint)
    a=3
