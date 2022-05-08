add r1 r0 24
sw dest r1
lw r2 dest
outb r2
outc '\n
add r2 r1 23
outb r2
outc '\n
halt
dest:
0
