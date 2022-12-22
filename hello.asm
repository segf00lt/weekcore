add r1 r0 data
loop:
lb r2 r1
out r1
beq r0 r2 end
add r1 r1 1
j loop
end:
halt
data:
"hello world\n\0"
