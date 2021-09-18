import json

opcodes = json.loads(open('../resources/opcodes.json').read())
opcodes_expanded = dict()
for opcode in opcodes:
    binary = opcodes[opcode]
    if len(binary) == 4:
        for i in range(16):
            binary = opcodes[opcode] + '{0:04b}'.format(i)
            opcodes_expanded[opcode + str(i)] = int(binary, 2)
    else:
        opcodes_expanded[opcode] = int(binary, 2)

md_table = "| Mnemonic, Operands | 8-bit Opcode | Decimal Opcode | \n" \
           "| :------ | :------ | ------: | \n"
opcodes_used = []
for opcode in sorted(opcodes_expanded, key=opcodes_expanded.get):
    md_table_row = "| " + opcode + " | " + \
                   '{0:08b}'.format(opcodes_expanded[opcode]) + " | " \
                   + str(opcodes_expanded[opcode]) + " | \n"
    md_table = md_table + md_table_row
    opcodes_used.append(opcodes_expanded[opcode])

print(md_table)

opcode_remaining = dict()
for i in range(1, 255):
    if i not in opcodes_used:
        opcode_remaining[i] = '{0:08b}'.format(i)
print(opcode_remaining)
