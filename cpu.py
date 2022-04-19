#!/usr/bin/env python3

from os import argv
from enum import Enum

class Op(Enum):
    NOP     = 0b000

    OP		= 0b001
    IMM		= 0b010

    JUMP	= 0b011 # takes constant value
    JUMPR	= 0b100 # reads value from register
    BRANCH	= 0b101

    LOAD	= 0b110
    STORE	= 0b111

class Funct(Enum):
    # OP and IMM
    ADD		= 0b000
    SUB		= 0b001
    AND		= 0b010
    OR		= 0b011
    XOR		= 0b100
    LSHIFT  = 0b101
    MUL     = 0b110
    DIV     = 0b111

    # BRANCH
    EQ		= 0b000
    NE		= 0b001
    LT		= 0b010
    GTE	    = 0b011

    # LOAD and STORE
    BYTE    = 0b000
    HWORD   = 0b001
    WORD    = 0b010

class Mask(Enum):
    OPCODE  = 0b111
    FUNCT   = 0b111
    REG     = 0b11111
    OFF_24  = 0b111111111111111111111111
    OFF_19  = 0b1111111111111111111
    OFF_7  = 0b1111111
    OFF_18  = 0b111111111111111111


# 33 registers:
# 1 zero register, 31 general purpose and a program counter
regnames = ['x0'] + [f'x{i}' for i in range(1, 32)] + ['PC']
PC = 32
regfile = None
memory = None

def reset():
    global regfile, memory
    regfile = [0] * 33
    memory = [0] * 8000

def alu(funct, x, y):
    if funct == Funct.ADD:
        return x + y
    elif funct == Funct.SUB:
        return x - y
    elif funct == Funct.AND:
        return x & y
    elif funct == Funct.OR:
        return x | y
    elif funct == Funct.XOR:
        return x ^ y
    elif funct == Funct.LSHIFT:
        return x << y
    elif funct == Funct.MUL:
        return x * y
    elif funct == Funct.DIV:
        return x / y

def cond(funct, x, y):
    ret = False
    if funct == Funct.EQ:
        ret = x == y
    elif funct == Funct.NE:
        ret = x != y
    elif funct == Funct.LT:
        ret = x < y
    elif funct == Funct.GTE:
        ret = x >= y
    return ret

def decode(inst, offset, mask):
    return inst & (mask << offset)

### INSTRUCTION LAYOUTS ###
#
# inst layout for int reg-reg operations (OP)
# 0      2  3      5  6       10  11      12  13      17  18                    31
# [opcode]  [funct ]  [dest    ]  [reg1    ]  [reg2    ]  [empty                 ]
#
# inst layout for int reg-imm operations (IMM)
# 0      2  3      5  6       10  11      12  13                                31
# [opcode]  [funct ]  [dest    ]  [reg1    ]  [imm       (const int val)         ]
#
# inst layout for imm-uncond-ctrl transfer operations (JUMP)
# 0      2  3       7  8                                                        31
# [opcode]  [dest   ]  [offset (24 bits)                                         ]
#
# inst layout for uncond-ctrl transfer operations (JUMPR)
# 0      2  3       7  8      12  13                                            31
# [opcode]  [dest   ]  [base   ]  [offset (19 bits)                              ]
#
# inst layout for cond-ctrl transfer operations (BRANCH)
# 0      2  3      5  8      12  13    17  18               24  25              31
# [opcode]  [funct ]  [reg1   ]  [reg2  ]  [offset (7 bits)  ]  [offset (7 bits) ]
#
# inst layout for memory access operations (LOAD, STORE)
# 0      2  3      5  6      10  9      13  14                                  31
# [opcode]  [funct ]  [reg    ]  [base   ]  [offset (18 bits)                    ]

def step():
    # fetch
    inst = regfile[PC]

    # decode
    opcode = decode(inst, 0, Mask.OPCODE)
    funct = decode(inst, 3, Mask.FUNCT)

    
    if opcode == Op.NOP:
        # skip to next instruction
    elif opcode == Op.OP:
    elif opcode == Op.IMM:
    elif opcode == Op.JUMP:
    elif opcode == Op.JUMPR:
    elif opcode == Op.BRANCH:
    elif opcode == Op.LOAD:
    elif opcode == Op.STORE:

    # execute

    # write



if __name__ == '__main__':
    print('yes')
