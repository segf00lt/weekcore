#!/usr/bin/env python3

from sys import stderr, argv
from cpu import Op, Fn, regnames

# read file and strip comments and whitespace
f = open(argv[1], 'r')
code = f.readlines()
code = [l.strip() for l in code if l[0] != '#' and l[0] != '\n']
f.close()

# assembler pass 1
tab = {}
pending = []
n = 0
tmp = []
for i,l in enumerate(code):
    if l[-1] == ':':
        pending += [l]
        n += 1
        continue
    while pending:
        tab[pending.pop()[:-1]] = i - n # multiply by 4 for byte addressable memory
    tmp += [l]
code = tmp

# assembler pass 2
print(tab)
print(code)

def geninst(op, fn, r_a=0, r_b=0, r_c=0, imm_s=0, imm_i=0):
    return op << 29 | fn << 26 | r_a << 21 | r_b << 16 | r_c << 11 | imm_s | imm_i

ctl = ['halt', 'nop']
io = ['iw', 'ow']
alur = ['add', 'sub', 'and', 'or', 'xor', 'not', 'ls', 'rs', 'mul', 'div']
jump = ['j', 'jal', 'jalr']
branch = ['beq', 'bne', 'blt', 'bgt', 'ble', 'bge']
mem = ['lw', 'sw']
