.createfile "bin/anim_expansion", MAIN_ADDRESS
.func anim_expansion
    li      at, ANIM_LOAD_ADD
    slt     at, v1, at
    beq     at, zero, end
    nop
    li      a1, ANIM_LOAD_ADD
    addiu   v1, a1, -0x14
    addiu   a2, v1, 0x2
    j       HOOK_ADD-0x30
    nop
end:
    lw      s3, 0xC(sp)
    j       HOOK_ADD+8
    lw      ra, 0x10(sp)
.endfunc

.warning org()
.close

.createfile "bin/hook", HOOK_ADD
    j       anim_expansion
    nop
.close
