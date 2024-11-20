.psp


.createfile "bin/anim_expansion", 0x08800700
    lui     at, 0x999
    slt     at, v1, at
    beq     at, zero, end
    nop
    lui     a1, 0x999
    addiu   v1, a1, -0x14
    addiu   a2, v1, 0x2
    j       0x088A4334
    nop
end:
    lw      s3, 0xC(sp)
    j       0x088A436C
    lw      ra, 0x10(sp)
.close

.createfile "bin/hook", 0x088A4364
    j       0x8800700
    nop
.close
