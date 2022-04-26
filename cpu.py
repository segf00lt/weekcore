#!/usr/bin/env python3

from sys import argv, stderr
from enum import Enum

class Op(Enum):
    CTL         = 0b000
    IO          = 0b001
    ALUR	    = 0b010 # register-register ALU operation
    ALUI	    = 0b011 # register-immediate ALU operation
    JUMP	    = 0b100
    BRANCH	    = 0b101
    MEM         = 0b110

class Fn(Enum):
    # CTL
    HALT        = 0b000
    NOP         = 0b001

    # IO
    IW          = 0b000
    OW          = 0b001
    IB          = 0b010
    OB          = 0b011
    IH          = 0b100
    OH          = 0b101

    # ALUR and ALUI
    ADD         = 0b000
    SUB         = 0b001
    AND         = 0b010
    OR          = 0b011
    XOR         = 0b100
    LS          = 0b101
    RS          = 0b110

    # JUMP
    J           = 0b000
    JAL         = 0b001

    # BRANCH
    EQ          = 0b000
    NE          = 0b001
    LT          = 0b010
    GE          = 0b011

    # MEM
    LW          = 0b000
    SW          = 0b100
    LB          = 0b001
    SB          = 0b101
    LH          = 0b010
    SH          = 0b110

# 33 registers: 1 zero register, 31 general purpose and a program counter
regnames = ['r0'] + [f'r{i}' for i in range(1, 32)] + ['pc']
pc = 32
regfile = None
memory = None

def binload(handle):
    with open(handle, "rb") as f:
        data = bytes(f.read())
    prog = [int.from_bytes(data[i:i+4], 'big') for i in range(0, len(data), 4)]
    return prog

class Regfile:
    def __init__(self):
        self.regs = [0] * 33
    def __getitem__(self, key):
        return self.regs[key]
    def __setitem__(self, key, value):
        if key == 0:
            return
        self.regs[key] = value

def reset():
    global regfile, memory
    regfile = Regfile()
    # TODO make memory byte addressable
    memory = [0] * 1000

def progdump(prog):
    print('==progdump==')
    for i,p in enumerate(prog):
        print(f"{i}:\t" + "0b{:032b}".format(p))
    print('============')

def memdump():
    global memory
    print('==memdump==')
    for i,w in enumerate(memory):
        print(f'{i}:\t' + '0b{:032b}'.format(w))
    print('===========')

def regdump():
    global regfile
    print('==regdump==')
    for i,w in enumerate(regfile):
        print(f'{regnames[i]}:\t' + '0b{:032b}'.format(w))
    print('===========')

def alu(fn, x, y):
    if fn == Fn.ADD:
        return x + y
    elif fn == Fn.SUB:
        return x - y
    elif fn == Fn.AND:
        return x & y
    elif fn == Fn.OR:
        return x | y
    elif fn == Fn.XOR:
        return x ^ y
    elif fn == Fn.LS:
        return x << y
    elif fn == Fn.RS:
        return x >> y

def cond(fn, x, y):
    ret = False
    if fn == Fn.EQ:
        ret = x == y
    elif fn == Fn.NE:
        ret = x != y
    elif fn == Fn.LT:
        ret = x < y
    elif fn == Fn.GE:
        ret = x >= y
    return ret

def gf(i, s, e): # get field of inst between s and e
    return (i >> e) & ((1 << (s - e + 1)) - 1)

def sext(x, l): # sign extend
    if x >> (l - 1) == 1:
        return -((1 << l) - x)
    else:
        return x

def step():
    # fetch
    inst = memory[regfile[pc]]
    newpc = regfile[pc]

    # decode
    op = Op(gf(inst, 31, 29))
    fn = Fn(gf(inst, 28, 26))
    r_a = gf(inst, 25, 21)
    r_b = gf(inst, 20, 16)
    r_c = gf(inst, 15, 11)
    imm_s = sext(gf(inst, 20, 0), 21)
    imm_i = sext(gf(inst, 15, 0), 16)

    # TODO refactor execute and write
    # execute
    if op == Op.CTL:
        if fn == Fn.HALT:
            return False
        else:
            newpc += 1
    elif op == Op.IO:
        if fn == Fn.IW:
            try:
                regfile[r_a] = int(input('<weekcore> ')) + imm_s
            except ValueError:
                print('error: non-integer input', file=stderr)
                exit(1)
        elif fn == Fn.OW:
            print(int(regfile[r_a]) + imm_s)
    elif op == Op.ALUR:
        regfile[r_a] = alu(fn, regfile[r_b], regfile[r_c])
    elif op == Op.ALUI:
        regfile[r_a] = alu(fn, regfile[r_b], imm_i)
    elif op == Op.JUMP:
        regfile[r_a] = regfile[pc]
        newpc = regfile[r_b] + imm_i
    elif op == Op.BRANCH:
        newpc += imm_i if cond(fn, regfile[r_a], regfile[r_b]) else 1
    elif op == Op.MEM:
        if fn == Fn.LW:
            regfile[r_a] = memory[regfile[r_b] + imm_i]
        elif fn == Fn.SW:
            memory[regfile[r_a]] = regfile[r_b]

    # write
    regfile[pc] = (newpc + 1) if newpc == regfile[pc] else newpc

    return True

if __name__ == '__main__':
    prog = binload(argv[1])
    reset()
    memory = prog + memory[len(prog):]
    while step():
        pass
