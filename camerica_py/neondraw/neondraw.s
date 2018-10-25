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
    // load offset into q14 so we can subtract from 8 pixels
    VDUP.16 q14, r2
    // and gain into d30 so we can multiply by 4 pixels
    VDUP.16 d30, r3
    // number of rows
    ldr r2, =256
    // number of bytes per row
    ldr r12, =(640*4)+(136*4)
    // pointer to second row of output
    add r3, r1, r12
    ldr r12, =(640*4)
merlin_loop:
merlin_row:
    // load 8 pixels from source to q0
    VLD1.16 {q0}, [r0]!
    // subtract offset from them and saturate so they don't go below 0
    VQSUB.U16 q1, q0, q14
    // apply scale factor too
    // widen into q2 and q3
    VMULL.U16 q2, d2, d30
    VMULL.U16 q3, d3, d30
    // now shift >> 15 to put intensity in low 8 bits
    // narrow to 16 bits and saturate too
    VQSHRN.U32 d16, q2, #15
    VQSHRN.U32 d17, q3, #15
    // narrow the pixels back down to 8 bits
    VQMOVN.U16 d24, q8
    // we have to duplicate the pixels horizontally
    VMOV d25, d24
    VZIP.8 d24, d25
    
    // now pack and write out groups of 8 pixels
    // first group will be 22, 23, 24, 25
    VMOV d22, d24
    VMOV d23, d24
    // we don't care what's in the alpha channel
    // write it on this output row
    VST4.8 {d22, d23, d24, d25}, [r1]!
    // and the next one
    VST4.8 {d22, d23, d24, d25}, [r3]!
    
    // do the second group in the same way
    // it will be 25, 26, 27, 28
    VMOV d26, d25
    VMOV d27, d25
    // write it on this output row
    VST4.8 {d25, d26, d27, d28}, [r1]!
    // and the next one
    VST4.8 {d25, d26, d27, d28}, [r3]!
    
    // out of pixels for this row?
    subs r12, r12, #64
    bne merlin_row
    
    ldr r12, =(640*4)+2*(136*4)
    // move both pointers to next row
    add r1, r1, r12
    add r3, r3, r12
    ldr r12, =(640*4)
    
    // now prepare for next iteration
    subs r2, r2, #1
    bne merlin_loop
    
    bx lr
    
