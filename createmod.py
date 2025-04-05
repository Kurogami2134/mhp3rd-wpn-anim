from sys import argv
from struct import pack

if "hd_ver" in argv:
    HOOK_ADD = 0x088A5C9C
    MAIN_ADDRESS = 0x0B000330
else:
    HOOK_ADD = 0x088A4364
    MAIN_ADDRESS = 0x08800800

with open("bin/anim_expansion", "rb") as main, open("bin/hook", "rb") as hook, open("bin/spanimexp.bin", "wb") as mod:
    data = main.read()
    mod.write(pack("2I", MAIN_ADDRESS, len(data)))
    mod.write(data)

    data = hook.read()
    mod.write(pack("2I", HOOK_ADD, len(data)))
    mod.write(data)

    mod.write(pack("2i", -1, 0))
