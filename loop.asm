add r2 r0 11
loop:
add r1 r1 2
bge r1 r2 end
j loop
end:
outd r1
outc '\n
halt
