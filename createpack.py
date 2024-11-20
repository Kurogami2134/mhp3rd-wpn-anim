from json import load
from anim_compiler import load_anim_entry, AnimExpansion

def main() -> None:
    with open("animations/included.json", "r", encoding="utf-8") as file:
        animations = load(file)

    Expansion = AnimExpansion()

    for anim, mdl_id in animations.items():
        Expansion.entries.append(load_anim_entry(f"animations/{anim}.json"))
        Expansion.entries[-1].mdl_id = mdl_id
    
    with open("bin/spanimpack.bin", "wb") as file:
        file.write(Expansion.build())


if __name__ == "__main__":
    main()
