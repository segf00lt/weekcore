#!/usr/bin/env python3

from sys import stderr, argv
from cpu import Op, Fn, regnames, scont
from re import compile as recomp

def progdump(prog):
    print('==progdump==')
    for i in range(0, len(prog), 4):
        inst = int.from_bytes(prog[i:i+4], 'big')
        print(f'{i//4}:\t' + '0b' + '_'.join(['{:032b}'.format(inst)[i:i+8] for i in range(0,32,8)]))
    print('============')

# read file and strip comments and whitespace
name = argv[1]
if not name.endswith('.asm'):
    raise Exception(f"bad file {name}")
f = open(name, 'r')
code = f.readlines()
code = [l.strip() for l in code if l[0] != '#' and l[0] != '\n']
f.close()

# store label locations
labeltab = {}
pending = []
prev = 0 # num bytes in program up to label
cur = 0 # num bytes from label to end of inst or literal
tmp = []
for l in code:
    if l[-1] == ':':
        pending += [l]
        continue
    else:
        prev = cur
        if l[0] == '\'':
            cur += 1
        elif l[0] == '\"':
            cur += len(bytes(l, 'utf8').decode('unicode_escape')) - 2
        else:
            cur += 4
    while pending:
        labeltab[pending.pop()[:-1]] = prev
    tmp += [l]
code = tmp
while pending:
    labeltab[pending.pop()[:-1]] = prev

# replace labels with values
for i,l in enumerate(code):
    l = l.split()
    for j,t in enumerate(l):
        try:
            l[j] = str(labeltab[t])
        except KeyError:
            l[j] = t
    code[i] = ' '.join(l)

# parsing and codegen
def geninst(op, fn, regs, imm):
    return op << 29 | fn << 26 | regs[0] << 21 | regs[1] << 16 | regs[2] << 11 | imm

# grammar
dnum = '-?[0-9]+'
bnum = '0b[01]+'
hnum = '0x[0-9a-f]+'
string = '\".+\"'
char = f"\'."
escape = "\\'\\\[ntr\\\]"
num = f"({dnum}|{bnum}|{hnum}|{char}|{escape})"
lit = f"({dnum}|{bnum}|{hnum}|{string}|{char}|{escape})"
reg = '(pc|r[0-9][0-9]*)'
ctl = '(halt|nop)'
io = '(in|out|outd|outb|outh|outc)'
alu = '(add|sub|and|or|xor|ls|rs)'
md = '(mul|div|mod)'
jump = '(j|jal)'
branch = '(beq|bne|blt|bge)'
load = '(l[whb])'
store = '(s[whb])'

optab = [("(halt|nop)", Op.CTL), (f"(sleep) {reg}", Op.CTL), (f"(sleep) {num}", Op.CTL),
        (lit, None),
        (f"{io} {reg}", Op.IO), (f"{io} {num}", Op.IO),
        (f"(clear)", Op.IO),
        (f"(in|out) {reg} {reg}", Op.IO),
        (f"{alu} {reg} {reg} {reg}", Op.ALUR), (f"{alu} {reg} {reg} {num}", Op.ALUI),
        (f"{md} {reg} {reg} {reg}", Op.MD),
        (f"{jump} {reg}", Op.JUMP), (f"{jump} {num}", Op.JUMP),
        (f"{jump} {reg} {reg}", Op.JUMP), (f"{jump} {reg} {num}", Op.JUMP),
        (f"{branch} {reg} {reg} {num}", Op.BRANCH),
        (f"{load} {reg} {reg}", Op.MEM),
        (f"{store} {reg} {reg}", Op.MEM),
        (f"{load} {reg} {num}", Op.MEM),
        (f"{store} {num} {reg}", Op.MEM)]

optab = [(recomp(t[0]), t[1]) for t in optab]

fntab = {'halt': Fn.HALT, 'nop': Fn.NOP, 'sleep': Fn.SLEEP,
        'in': Fn.IN, 'out': Fn.OUT, 'outd': Fn.OUTD, 'outb': Fn.OUTB, 'outh': Fn.OUTH, 'outc': Fn.OUTC,
        'clear': Fn.CL,
        'add': Fn.ADD, 'sub': Fn.SUB, 'and': Fn.AND, 'or': Fn.OR, 'xor': Fn.XOR, 'ls': Fn.LS, 'rs': Fn.RS,
        'mul': Fn.MUL, 'div': Fn.DIV, 'mod': Fn.MOD,
        'j': Fn.J, 'jal': Fn.JAL,
        'beq': Fn.EQ, 'bne': Fn.NE, 'blt': Fn.LT, 'bge': Fn.GE,
        'lw': Fn.LW, 'lh': Fn.LH, 'lb': Fn.LB, 'sw': Fn.SW, 'sh': Fn.SH, 'sb': Fn.SB}

regtab = {r: i for i,r in enumerate(regnames)}

prog = b''
for _,l in enumerate(code):
    m = None
    op = None
    fn = None
    regs = []
    imm = 0
    immlen = 0
    bytecat = lambda a,b: b''.join([a, b])

    for _,ent in enumerate(optab):
        if m := ent[0].fullmatch(l):
            try:
                op = ent[1].value
            except AttributeError: # literal value
                op = None
                value = b''
                if l[0] == '"':
                    value = bytes(bytes(l[1:-1], 'utf8').decode('unicode_escape'), 'utf8')
                elif l[:-1] == '\'\\':
                    value = bytes(bytes(l[1:], 'utf8').decode('unicode_escape'), 'utf8')
                elif l[0] == '\'':
                    value = ord(l[1]).to_bytes(1, 'big')
                elif l[:2] == '0b':
                    value = int(l, base=2).to_bytes(4, 'big')
                elif l[:2] == '0x':
                    value = int(l, base=16).to_bytes(4, 'big')
                else:
                    value = int(l, base=10).to_bytes(4, 'big')
                prog = bytecat(prog, value)
            break

    if not m:
        raise Exception(f"bad instruction {l}")

    if op is None:
        continue

    fn = fntab[m.group(1)].value
    immlen = 20 if op in [Op.CTL, Op.IO] else 16

    for g in m.groups()[1:]:
        try:
            regs += [regtab[g]]
        except KeyError:
            regs += [0]
            if g[:-1] == '\'\\':
                imm = scont(ord(bytes(g[1:], 'utf8').decode('unicode_escape')), immlen)
            elif g[0] == '\'':
                imm = scont(ord(g[1]), immlen)
            elif g[:2] == '0b':
                imm = scont(int(g, base=2), immlen)
            elif g[:2] == '0x':
                imm = scont(int(g, base=16), immlen)
            else:
                imm = scont(int(g, base=10), immlen)
    regs += [0] * (3 - len(regs))
    inst = geninst(op, fn, regs, imm).to_bytes(4, 'big')
    prog = bytecat(prog, inst)

progdump(prog)
# write executable
with open('a.out', 'wb') as file:
    file.write(prog)
