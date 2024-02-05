import json
from pathlib import Path

RESOURCE_FOLDER = Path(__file__).parent.parent.parent / "resources"


class InstructionDecoder:
    @staticmethod
    def load_opcode_map():
        with open(RESOURCE_FOLDER / "opcodes.json") as opcode_file:
            opcodes = json.loads(opcode_file.read())

        opcodes_expanded = dict()
        for opcode in opcodes:
            binary = opcodes[opcode]
            if len(binary) == 4:
                for i in range(16):
                    binary = opcodes[opcode] + '{0:04b}'.format(i)
                    opcodes_expanded[opcode + str(i)] = int(binary, 2)
            else:
                opcodes_expanded[opcode] = int(binary, 2)

        return {v: k for k, v in opcodes_expanded.items()}

    @staticmethod
    def decode_all_instructions(binary):
        opcode_map = InstructionDecoder.load_opcode_map()

        decoded_instructions = []
        for instruction in binary:
            literal_binary = instruction[:24]
            opcode_binary = instruction[24:]

            literal = int(literal_binary, 2)
            opcode = opcode_map[int(opcode_binary, 2)]
            decoded_instructions.append((opcode, literal))
        return decoded_instructions
