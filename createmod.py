from struct import pack

with open("bin/anim_expansion", "rb") as main, open("bin/hook", "rb") as hook, open("bin/spanimexp.bin", "wb") as mod:
    data = main.read()
    mod.write(pack("2I", 0x08800800, len(data)))
    mod.write(data)

    data = hook.read()
    mod.write(pack("2I", 0x088A4364, len(data)))
    mod.write(data)

    mod.write(pack("2i", -1, 0))
