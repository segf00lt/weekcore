#!/usr/bin/env python3

from sys import stderr, argv
from cpu import Op, Fn, regnames, progdump
from re import compile as recomp
from binascii import hexlify

# read file and strip comments and whitespace
f = open(argv[1], 'r')
code = f.readlines()
code = [l.strip() for l in code if l[0] != '#' and l[0] != '\n']
f.close()

# assembler pass 1
labeltab = {}
pending = []
n = 0
tmp = []
for i,l in enumerate(code):
    if l[-1] == ':':
        pending += [l]
        n += 1
        continue
    while pending:
        labeltab[pending.pop()[:-1]] = i - n # multiply by 4 for byte addressable memory
    tmp += [l]
code = tmp

# assembler pass 2
for i,l in enumerate(code):
    l = l.split()
    for j,t in enumerate(l):
        try:
            l[j] = str(labeltab[t])
        except KeyError:
            l[j] = t
    code[i] = ' '.join(l)

# assembler pass 3
def geninst(op, fn, regs, imm):
    return op << 29 | fn << 26 | regs[0] << 21 | regs[1] << 16 | regs[2] << 11 | imm

# grammar
reg = '(pc|r[0-9][0-9]*)'
num = '(-?[0-9]+)'
ctl = '(halt|nop)'
io = '([io][whb])'
alu = '(add|sub|and|or|xor|ls|rs|mul|div)'
jump = '(j|jal)'
branch = '(beq|bne|blt|bge)'
mem = '([ls][whb])'

optab = [(ctl, Op.CTL),
         (f"{io} {reg}", Op.IO), (f"{io} {num}", Op.IO),
         (f"{alu} {reg} {reg} {reg}", Op.ALUR), (f"{alu} {reg} {reg} {num}", Op.ALUI),
         (f"{jump} {reg}", Op.JUMP), (f"{jump} {num}", Op.JUMP),
         (f"{jump} {reg} {reg}", Op.JUMP), (f"{jump} {reg} {num}", Op.JUMP),
         (f"{branch} {reg} {reg} {num}", Op.BRANCH),
         (f"{mem} {reg} {reg}", Op.MEM), (f"{mem} {reg} {num}", Op.MEM)]

optab = [(recomp(t[0]), t[1]) for t in optab]

fntab = {'halt': Fn.HALT, 'nop': Fn.NOP,
         'iw': Fn.IW, 'ih': Fn.IH, 'ib': Fn.IB, 'ow': Fn.OW, 'oh': Fn.OH, 'ob': Fn.OB,
         'add': Fn.ADD, 'sub': Fn.SUB, 'and': Fn.AND, 'or': Fn.OR, 'xor': Fn.XOR, 'ls': Fn.LS, 'rs': Fn.RS,
         'j': Fn.J, 'jal': Fn.JAL,
         'beq': Fn.EQ, 'bne': Fn.NE, 'blt': Fn.LT, 'bge': Fn.GE,
         'lw': Fn.LW, 'lh': Fn.LH, 'lb': Fn.LB, 'sw': Fn.SW, 'sh': Fn.SH, 'sb': Fn.SB}

regtab = {r: i for i,r in enumerate(regnames)}

prog = []
for _,l in enumerate(code):
    m = None
    op = None
    fn = None
    regs = []
    imm = 0

    for _,ent in enumerate(optab):
        if m := ent[0].fullmatch(l):
            op = ent[1].value
            break

    if not m:
        print(f"error: bad instruction: {l}", file=stderr)
        exit(1)

    fn = fntab[m.group(1)].value

    for g in m.groups()[1:]:
        try:
            regs += [regtab[g]]
        except KeyError:
            imm = int(g)
    regs += [0] * (3 - len(regs)) # pad with zeros if needed
    prog += [geninst(op, fn, regs, imm)]

progdump(prog)
# write executable
aout = [i.to_bytes(4, 'big') for i in prog]
with open('a.out', 'wb') as file:
    for a in aout:
        file.write(a)
    file.close()
