#!/usr/bin/env python3

from sys import argv, stderr, stdin, stdout
from time import sleep
from os import system
from struct import pack, unpack
from enum import Enum

class Op(Enum):
    CTL         = 0b000
    IO          = 0b001
    ALUR	    = 0b010 # register-register ALU operation
    ALUI	    = 0b011 # register-immediate ALU operation
    MD          = 0b100 # register-register multiply or divide operation
    JUMP	    = 0b101
    BRANCH	    = 0b110
    MEM         = 0b111

class Fn(Enum):
    # CTL
    HALT        = 0b000
    NOP         = 0b001
    SLEEP       = 0b010

    # IO
    IN          = 0b000
    OUT         = 0b001
    OUTD        = 0b010 # output reg or imm as decimal number
    OUTB        = 0b011 # output reg or imm as binary number
    OUTH        = 0b100 # output reg or imm as hex number
    OUTC        = 0b101 # output reg or imm as character
    CL          = 0b110 # clear output

    # ALUR and ALUI
    ADD         = 0b000
    SUB         = 0b001
    AND         = 0b010
    OR          = 0b011
    XOR         = 0b100
    LS          = 0b101
    RS          = 0b110

    # MD
    MUL         = 0b000
    DIV         = 0b001
    MOD         = 0b010

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
        return bytes(f.read())

def memr(begin, end): # unpack data for loads
    global memory
    test = lambda x: x < 0 or (x + 1) >= len(memory)
    if test(begin) or test(end):
        raise Exception(f"memory address {hex(addr)} out of bounds")
    return memory[begin:end if end != 0 else begin + 1]

def memw(addr, data): # must pack data
    global memory
    l = len(data)
    if addr < 0 or (addr + l) >= len(memory):
        raise Exception(f"memory address {hex(addr)} out of bounds")
    memory = memory[:addr] + data + memory[addr+l:]

def gf(i, s, e): # get field of inst between s and e
    return (i >> e) & ((1 << (s - e + 1)) - 1)

def scont(x, l): # sign contract
    return x & ((1 << l) - 1)

def sext(x, l): # sign extend
    if x >> (l - 1) == 1:
        return -((1 << l) - x)
    else:
        return x

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
    memory = b'\x00' * 8000

def regdump():
    global regfile
    print('==regdump==')
    for i,w in enumerate(regfile):
        print(f'{regnames[i]}:\t' + '0b' + \
                '_'.join(['{:032b}'.format(w)[i:i+8] for i in range(0,32,8)]))
    print('===========')

def instdump(inst):
    print('==instdump==')
    print('0b' + '_'.join(['{:032b}'.format(inst)[i:i+8] for i in range(0,32,8)]))
    print('============')

def io(fn, x, y, z):
    if fn == Fn.IN:
        n = 1 if y == 0 else y - x
        memw(x + z, bytes(stdin.read(n), 'utf8'))
    elif fn == Fn.OUT:
        stdout.write(memr(x + z, y).decode('unicode_escape'))
    elif fn == Fn.OUTD:
        stdout.write('{:d}'.format(sext(x + z, 32))) # keep sign
    elif fn == Fn.OUTB:
        stdout.write('0b{:032b}'.format(scont(x + z, 32)))
    elif fn == Fn.OUTH:
        stdout.write('0x{:08x}'.format(scont(x + z, 32)))
    elif fn == Fn.OUTC:
        stdout.write(chr(x + z))
    else:
        system('clear')


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

def muldiv(fn, x, y):
    if fn == Fn.MUL:
        return x * y
    elif fn == Fn.DIV:
        return x // y
    elif fn == Fn.MOD:
        return x % y

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

def step():
    # fetch
    inst = unpack('>I', memr(regfile[pc], regfile[pc] + 4))[0]
    newpc = regfile[pc]

    # decode
    op = Op(gf(inst, 31, 29))
    fn = Fn(gf(inst, 28, 26))
    r_a = gf(inst, 25, 21)
    r_b = gf(inst, 20, 16)
    r_c = gf(inst, 15, 11)
    imm = sext(gf(inst, 15, 0), 16)

    # TODO refactor execute and write
    # execute
    if op == Op.CTL:
        if fn == Fn.HALT:
            return False
        elif fn == Fn.NOP:
            newpc += 1
        else:
            sleep(regfile[r_a] + imm)
    elif op == Op.IO:
        io(fn, regfile[r_a], regfile[r_b], imm)
    elif op == Op.ALUR:
        regfile[r_a] = alu(fn, regfile[r_b], regfile[r_c])
    elif op == Op.ALUI:
        regfile[r_a] = alu(fn, regfile[r_b], imm)
    elif op == Op.MD:
        regfile[r_a] = muldiv(fn, regfile[r_b], regfile[r_c])
    elif op == Op.JUMP:
        regfile[r_a] = regfile[pc]
        newpc = regfile[r_b] + imm
    elif op == Op.BRANCH:
        newpc = imm if cond(fn, regfile[r_a], regfile[r_b]) else newpc
    elif op == Op.MEM:
        laddr = regfile[r_b] + imm
        if fn == Fn.LW:
            regfile[r_a] = unpack('>I', memr(laddr, laddr + 4))[0]
        elif fn == Fn.LB:
            regfile[r_a] = unpack('>B', memr(laddr, laddr + 1))[0]
        elif fn == Fn.LH:
            regfile[r_a] = unpack('>H', memr(laddr, laddr + 2))[0]
        elif fn == Fn.SW:
            memw(regfile[r_a] + imm, pack('>I', regfile[r_b] & 0xffffffff))
        elif fn == Fn.SB:
            memw(regfile[r_a] + imm, pack('>B', regfile[r_b] & 0xff000000))
        elif fn == Fn.SH:
            memw(regfile[r_a] + imm, pack('>H', regfile[r_b] & 0xffff0000))

    # write
    regfile[pc] = (newpc + 4) if newpc == regfile[pc] else newpc

    return True

if __name__ == '__main__':
    prog = binload(argv[1])
    reset()
    memory = prog + memory[len(prog):]
    while step():
        pass
