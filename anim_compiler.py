from sys import argv
from json import load
from struct import pack


if "hd_ver" in argv:
    ANIM_LOAD_ADD = 0x0B000400
else:
    ANIM_LOAD_ADD = 0x099C0000

with open("anim_types.json", "r", encoding="utf-8") as file:
    ANIM_TYPES = load(file)


WPN_TYPES = {
    "GS": 0,
    "SNS": 1,
    "HMR": 2,
    "LNC": 3,
    "HBG": 4,
    "LBG": 6,
    "LS": 7,
    "SAXE": 8,
    "GL": 9,
    "BOW": 10,
    "DB": 11,
    "HH": 12
}


class Anim:
    def __init__(self) -> None:
        self.frames: list[int] = [0, 0, 0, 0, 0, 0]
        self.bone: int = 0
        self.type: int = 0
        self.mdl = False

    @property
    def data(self) -> bytes:
        return pack("<2BxB6i", ANIM_TYPES["MODEL" if self.mdl else "TEXTURE"][self.type], self.bone, 3, *self.frames)


class AnimEntry:
    def __init__(self) -> None:
        self.model: list[Anim] = []
        self.texture: list[Anim] = []
        self.data_add: int
        self.wpn_type: str
        self.mdl_id: int
    
    @property
    def mdl_anim_count(self) -> int:
        return len(self.model)
    
    @property
    def tex_anim_count(self) -> int:
        return len(self.texture)

    @property
    def model_add(self) -> int:
        return self.data_add if self.mdl_anim_count else 0
    
    @property
    def tex_add(self) -> int:
        return (self.data_add + self.mdl_anim_count * 28) if self.tex_anim_count else 0
    
    @property
    def anim_data(self) -> bytes:
        data = b''
        for anim in self.model:
            data += anim.data
        for anim in self.texture:
            data += anim.data
        
        return data

    def anim_entry(self, mdl_id: None | int = None, wpn_type: None | str = None) -> bytes:
        if wpn_type is None:
            wpn_type = self.wpn_type
        if mdl_id is None:
            mdl_id = self.mdl_id
        return pack("<H4B2x3I", WPN_TYPES[wpn_type.upper()], mdl_id, self.mdl_anim_count, self.tex_anim_count, 0, self.model_add, self.tex_add, 0)


class AnimExpansion:
    def __init__(self) -> None:
        self.entries: list[AnimEntry] = []
    
    def build(self, entry_add: int = ANIM_LOAD_ADD) -> bytes:
        start: int = entry_add
        entries: bytes = b''
        anim: bytes = b''

        anim_add: int = entry_add + len(self.entries) * 0x14 + 4
        for entry in self.entries:
            entry.data_add = anim_add
            entries += entry.anim_entry()
            anim += entry.anim_data

            anim_add += (entry.mdl_anim_count + entry.tex_anim_count) * 28
            entry_add += 0x14
        
        data = entries+b'\xFF\xFF\xFF\xFF'+anim
        data = pack("2i", start, len(data)) + data + pack("2i", -1, 0)
        
        return data


def load_anim(data) -> Anim:
    anim = Anim()
    anim.bone = data["bone"]
    anim.type = data["type"]
    anim.frames = data["keyframes"]

    return anim


def load_anim_entry(path) -> AnimEntry:
    with open(path, "r", encoding="utf-8") as file:
        data = load(file)
    entry = AnimEntry()
    entry.wpn_type = data["type"]
    for mdl in data["model"]:
        entry.model.append(load_anim(mdl))
        entry.model[-1].mdl = True
    for tex in data["texture"]:
        entry.texture.append(load_anim(tex))
        entry.texture[-1].mdl = False
    
    return entry
