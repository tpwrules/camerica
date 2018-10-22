.syntax unified
.thumb

.cpu cortex-a9

.text

.global nd_testadd1

nd_testadd1:
    add r0, r0, #1
    bx lr
