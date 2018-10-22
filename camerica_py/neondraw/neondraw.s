.syntax unified
.thumb

.cpu cortex-a9
.fpu neon

.text

.global nd_testadd1

nd_testadd1:
    add r0, r0, #1
    bx lr


.global nd_conv_merlin

// on entry
// r0 - source pointer
// r1 - dest pointer
// r2 - offset
// r3 - gain
// q4-q7 are off limits
nd_conv_merlin:
    // load offset into q8 so we can subtract from 8 pixels
    VDUP.16 q8, r2
    // and gain into d18 so we can multiply by 4 pixels
    VDUP.16 d18, r3
    // number of rows
    ldr r2, =256
    // number of bytes per row
    ldr r12, =(640*4)
    // pointer to second row of output
    add r3, r1, r12
merlin_loop:
merlin_row:
    // load 8 pixels from source to q0
    VLD1.16 {q0}, [r0]!
    // subtract offset from them and saturate so they don't go below 0
    VQSUB.U16 q0, q0, q8
    // apply scale factor too
    // widen into q1 and q2
    VMULL.U16 q1, d0, d18
    VMULL.U16 q2, d1, d18
    // now shift >> 15 to put intensity in low 8 bits
    // narrow to 16 bits and saturate too
    VQSHRN.U32 d2, q1, #15
    VQSHRN.U32 d4, q2, #15
    // we have to duplicate the pixels horizontally
    VMOV d3, d2
    VZIP.16 d3, d2
    VMOV d5, d4
    VZIP.16 d5, d4
    
    // now pack and write out groups of 8 pixels
    // narrow the first group
    VQMOVN.U16 d20, q1
    // and duplicate it for the green and blue
    VMOV d21, d20
    VMOV d22, d20
    // we don't care what's in the alpha channel
    
    // write it on this output row
    VST4.8 {d20, d21, d22, d23}, [r1]!
    // and the next one
    VST4.8 {d20, d21, d22, d23}, [r3]!
    
    // do the second group in the same way
    VQMOVN.U16 d20, q2
    // and duplicate it for the green and blue
    VMOV d21, d20
    VMOV d22, d20
    // we don't care what's in the alpha channel
    
    // write it on this output row
    VST4.8 {d20, d21, d22, d23}, [r1]!
    // and the next one
    VST4.8 {d20, d21, d22, d23}, [r3]!
    
    // out of pixels for this row?
    subs r12, r12, #64
    bne merlin_row
    
    ldr r12, =(640*4)
    // move both pointers to next row
    add r1, r1, r12
    add r3, r3, r12
    
    // now prepare for next iteration
    subs r2, r2, #1
    bne merlin_loop
    
    bx lr
    
