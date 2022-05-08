add r1 r0 1
add r2 r0 11
add r3 r0 2
loop:
mul r1 r1 r3
bge r1 r2 end
j loop
end:
outd r1
outc '\n
halt
