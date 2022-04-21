#!/usr/bin/env python3

from sys import argv, stderr
from enum import Enum

class Op(Enum):
    SYS     = 0b000
    ALUR	= 0b001 # register-register ALU operation
    ALUI	= 0b010 # register-immediate ALU operation
    JUMP	= 0b011
    BRANCH	= 0b100
    MEM     = 0b101


class Fn(Enum):
    # SYS
    NOP         = 0b000
    HALT        = 0b001
    IN          = 0b010
    OUT         = 0b011

    # ALUR and ALUI
    ADD         = 0b000
    SUB         = 0b001
    AND         = 0b010
    OR          = 0b011
    XOR         = 0b100
    LSHIFT      = 0b101
    MUL         = 0b110
    DIV         = 0b111

    # JUMP
    REL         = 0b000
    ABS         = 0b001

    # BRANCH
    EQ          = 0b000
    NE          = 0b001
    LT          = 0b010
    GTE         = 0b011

    # MEM
    LOAD        = 0b000
    STORE       = 0b001

# 33 registers:
# 1 zero register, 31 general purpose and a program counter
regnames = ['r0'] + [f'r{i}' for i in range(1, 32)] + ['pc']
pc = 32
word = 4 # bytes
regfile = None
memory = None

def reset():
    global regfile, memory
    regfile = [0] * 33
    memory = [0] * 1000 # memory is word addressable

def ctl(fn, x):
    if fn == Fn.HALT:
        return False
    elif fn == Fn.NOP:
        regfile[PC] += word
    else:
        io(fn, x)
    return True

def io(fn, x):
    if fn == Fn.IN:
        try:
            regfile[x] = int(input('<weekcore> '))
        except ValueError:
            print('error: non-integer input', file=sys.stderr)
            exit(1)
    elif fn == Fn.OUT:
        print(int(regfile[x]))

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
    elif fn == Fn.LSHIFT:
        return x << y
    elif fn == Fn.MUL:
        return x * y
    elif fn == Fn.DIV:
        return x / y

def cond(fn, x, y):
    ret = False
    if fn == Fn.EQ:
        ret = x == y
    elif fn == Fn.NE:
        ret = x != y
    elif fn == Fn.LT:
        ret = x < y
    elif fn == Fn.GTE:
        ret = x >= y
    return ret

def mem(fn, x, y):
    if fn == Fn.LOAD:
        regfile[x] = memory[regfile[y]]
    elif fn == Fn.STORE:
        memory[regfile[x]] = regfile[y]

def field(i, s, e): # get field of inst between s and e
    return (i >> e) & ((1 << (s - e + 1)) - 1)

def sext(x, l): # sign extend
    if x >> (l - 1) == 1:
        return -((1 << l) - x)
    else:
        return x

def step():
    # fetch
    inst = memory[regfile[PC]]
    stat = True

    # decode
    op = field(inst, 31, 29)
    fn = field(inst, 28, 24)
    r_a = field(inst, 23, 19)
    r_b = field(inst, 18, 14)
    r_c = field(inst, 13, 9)
    imm_s = sext(field(inst, 18, 0))
    imm_i = sext(field(inst, 13, 0))
    imm_b1 = sext(field(inst, 13, 7))
    imm_b2 = sext(field(inst, 6, 0))

    # execute
    if op == Op.SYS:
        stat = ctl(fn, r_a)
    elif op == Op.ALUR:
        regfile[r_a] = alu(fn, regfile[r_b], regfile[r_c])
    elif op == Op.ALUI:
        regfile[r_a] = alu(fn, regfile[r_b], imm_i)
    elif op == Op.JUMP:
        regfile[r_a] = regfile[pc]
        regfile[pc] = regfile[r_b] if fn == Fn.ABS else (regfile[pc] + imm_i * 4)
    elif op == Op.BRANCH:
        regfile[pc] += 4 * (imm_b1 if cond(fn, regfile[r_a], regfile[r_b]) else imm_b2)
    elif op == Op.MEM:
        mem(fn, r_a, r_b)

    # write
    # not really a stage yet, will be done after pipeline refactor



if __name__ == '__main__':
    print('yes')
