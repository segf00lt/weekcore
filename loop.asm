add r2 r0 10
loop:
add r1 r1 2
beq r1 r2 end
j loop
end:
ow r1
halt
