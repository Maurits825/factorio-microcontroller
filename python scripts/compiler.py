"""
compiler for the gg assembly language
"""

import json


def compileGG():
    codefile = open('../programs/test.txt', 'r')

    rawcode = list()
    binarycode = list()
    hexcode = list()
    addrf = {}
    labels = {}

    opcode = json.loads(open('../resources/opcodes.json').read())
    codeline = codefile.readlines()

    i = 0
    for line in codeline:
        if '#' not in line:
            # remove comments
            splitline = codeline[i].rstrip().split()
            if splitline:
                # remove white space
                if '%' in line:
                    # add f memory address names
                    addrf[splitline[1]] = splitline[2].replace('0b', '')

                elif len(splitline) == 1:
                    # goto label
                    labels[splitline[0]] = format(len(rawcode), '016b')

                # Bit test
                elif 'BTS' in splitline[0]:
                    BT = splitline[0].split(',')
                    BT[1] = format(int(BT[1]), '04b') + \
                        splitline[1].replace('0b', '')
                    rawcode.append(BT)

                # Bit set and clear
                elif 'BS' in splitline[0] or 'BC' in splitline[0]:
                    BT = splitline[0].split(',')
                    BT[1] = format(int(BT[1]), '04b') + \
                        splitline[1].replace('0b', '')
                    rawcode.append(BT)

                # literal values
                elif '0b' in splitline[1]:
                    splitline[1] = splitline[1].replace('0b', '')
                    rawcode.append(splitline)

                # replace goto label with binary
                elif splitline[0] == 'GOTO':
                    splitline[1] = labels[splitline[1]]
                    rawcode.append(splitline)

                # addr names
                else:
                    splitline[1] = addrf[splitline[1]]
                    rawcode.append(splitline)
        i = i + 1

    # print('Raw code:', rawcode)

    i = 0
    for line in rawcode:
        binarycode.append(opcode[rawcode[i][0]] + rawcode[i][1])
        i = i + 1

    i = 0
    for line in binarycode:
        hexcode.append('%06X' % int(binarycode[i], 2))
        i = i + 1
    # print('Hex code:', hexcode)

    i = 0
    Hexfile = open('../programs/hexcode_16_bit.txt', 'w')
    for line in hexcode:
        Hexfile.write(hexcode[i] + '\n')
        i = i + 1

    Hexfile.close()
    codefile.close()

compileGG()
