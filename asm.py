#!/usr/bin/env python3

from sys import stderr, argv
from cpu import InstType, Op, Fn, regnames

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
def genhead(op, fn):
    return op << 29 | fn << 26

def geninst(head, r_a=0, r_b=0, r_c=0, imm_s=0, imm_i=0):
    return head | r_a << 21 | r_b << 16 | r_c << 11 | imm_s | imm_i

ctl = {'halt': Fn.HALT.value, 'nop': Fn.NOP.value,}
io = {'iw': Fn.IW.value, 'ow': Fn.OW.value,
        'ib': Fn.IB.value, 'ob': Fn.OB.value,
        'ih': Fn.IH.value, 'oh': Fn.OH.value,}
alur = {'add': Fn.ADD.value, 'sub': Fn.SUB.value,
        'and': Fn.AND.value, 'or': Fn.OR.value,
        'xor': Fn.XOR.value, 'ls': Fn.LS.value,
        'rs': Fn.LS.value, 'mul': Fn.MUL.value,
        'div': Fn.DIV.value, 'mov': Fn.ADD.value,}
alui = {'addi': Fn.ADD.value, 'subi': Fn.SUB.value,
        'andi': Fn.AND.value, 'ori': Fn.OR.value,
        'xori': Fn.XOR.value, 'lsi': Fn.LS.value,
        'rsi': Fn.LS.value, 'muli': Fn.MUL.value,
        'divi': Fn.DIV.value, 'movi': Fn.ADD.value,}
jump = {'j': Fn.J.value, 'jal': Fn.J.value, 'jalr': Fn.J.value,}
branch = {'beq': Fn.EQ.value, 'bne': Fn.NE.value, 'blt': Fn.LT.value,
        'bgt': Fn.LT.value, 'ble': Fn.GE.value, 'bge': Fn.GE.value,}
mem = {'lw': Fn.LW.value, 'sw': Fn.SW.value, 'lb': Fn.LB.value,
        'sb': Fn.SB.value, 'lh': Fn.LH.value, 'sh': Fn.SH.value,}

prog = []
for _,l in enumerate(code):
    token = l.split()
    print(l)
    operate = token[0]
    args = token[1:]
    head = 0
    inst = 0
    insttype = InstType.S
    # generate opcode and funct
    if operate in ctl:
        head = genhead(Op.CTL.value, ctl[operate])
    elif operate in io:
        head = genhead(Op.IO.value, io[operate])
    elif operate in alur:
        head = genhead(Op.ALUR.value, alur[operate])
        insttype = InstType.R
    elif operate in alui:
        head = genhead(Op.ALUI.value, alui[operate])
        insttype = InstType.I
    elif operate in jump:
        head = genhead(Op.JUMP.value, jump[operate])
        insttype = InstType.I
    elif operate in branch:
        head = genhead(Op.BRANCH.value, branch[operate])
        insttype = InstType.I
    elif operate in mem:
        head = genhead(Op.MEM.value, mem[operate])
        insttype = InstType.I
    # generate regs and imms
    imm = 0
    r = [0] * 3
    for i,a in enumerate(args):
        if i >= 3:
            print(f"error: too many arguments\nline: {''.join(l)}\n", file=stderr)
            exit(1)
        try:
            imm = int(a)
        except ValueError:
            try:
                r[i] = regnames.index(a)
            except ValueError:
                print(f"error: invalid argument {a}\nline: {''.join(l)}\n", file=stderr)
                exit(1)
    # build instruction
    match insttype:
        case InstType.S:
            inst = geninst(head, r_a=r[0], imm_s=imm)
        case InstType.R:
            inst = geninst(head, r_a=r[0], r_b=r[1], r_c=r[2])
        case InstType.I:
            inst = geninst(head, r_a=r[0], r_b=r[1], imm_i=imm)
    prog += [inst]

for i,p in enumerate(prog):
    print(f"{i}:\t" + "0b{:032b}".format(p))
