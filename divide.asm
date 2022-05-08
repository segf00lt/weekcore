add r1 r0 12
add r2 r0 6
add r3 r0 2
div r4 r1 r2
beq r3 r4 yes
halt
yes:
add r5 r0 str
add r6 r5 5
out r5 r6
halt
str:
"yes\n"
