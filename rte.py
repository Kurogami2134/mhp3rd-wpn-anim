from ModIO import PspRamIO
from json import load, dumps
from struct import pack, unpack
from typing import Any
from tkinter import *
from tkinter.ttk import *
from enum import Enum

class AnimType(Enum):
    Vertex = "Vertex"
    Texture = "Texture"

with open("anim_types.json", "r", encoding="utf-8") as file:
    ANIM_TYPES = load(file)

R_ANIM_TYPES = {
    "MODEL": {v: k for k, v in ANIM_TYPES["MODEL"].items()},
    "TEXTURE": {v: k for k, v in ANIM_TYPES["TEXTURE"].items()}
}
ANIM_LOAD = 0x099C0000
EQUIPPED_WEAPON = 0x09B49234
WEAPON_DATA = [
    None,
    None,
    None,
    None,
    None,
    (0x08992168, 0x1C),
    (0x0898FA78, 0x1C),
    (0x0898E71C, 0x1C),
    (0x08990D64, 0x1C),
    (0x0898AB2C, 0x50),
    None,
    (0x0898C01C, 0x50),
    (0x08991800, 0x1C),
    (0x0898D5D4, 0x1C),
    (0x089904DC, 0x1C),
    (0x089891DC, 0x50),
    (0x0898F164, 0x1C),
    (0x0898DDB4, 0x1C)
]
WPN_TYPES = {
    0: "gs",
    1: "sns",
    2: "hmr",
    3: "lnc",
    4: "hbg",
    6: "lbg",
    7: "ls",
    8: "saxe",
    9: "gl",
    10: "bow",
    11: "db",
    12: "hh"
}

ANIM_TYPE_RANGES = {
    "Texture": {
        "H_STRIDE": (0, 128),
        "V_STRIDE": (0, 128),
        "LUMA (SMOOTH)": (0, 255),
        "LUMA": (0, 255),
        "ALPHA": (0, 255),
        "RGB": (0, 1),
        "VISIBLE": (0, 1)
    },
    "Vertex": {
        "ROTATE_X": (0, 500),
        "ROTATE_Y": (0, 500),
        "ROTATE_Z": (0, 500),
        "ROTATION_X": (0, 4),
        "ROTATION_Y": (0, 4),
        "ROTATION_Z": (0, 4),
        "SCALE": (0, 300),
        "SCALE_XY": (0, 300),
        "SCALE_XZ": (0, 300),
        "SCALE_YZ": (0, 300),
        "SCALE_Z": (0, 300),
        "TRANSLATE_Y": (0, 500),
        "TRANSLATE_X": (0, 500),
        "TRANSLATE_Z": (0, 500)
    }
}

def get_model_id(ram: PspRamIO) -> int:
    wpn_type = get_weapon_type(ram)
    ram.seek(EQUIPPED_WEAPON + 2)
    wpn_id = unpack("b", ram.read(1))[0]
    ram.seek(WEAPON_DATA[wpn_type][0] + WEAPON_DATA[wpn_type][1] * wpn_id)
    return unpack("h", ram.read(2))[0]


def get_weapon_type(ram: PspRamIO) -> int:
    ram.seek(EQUIPPED_WEAPON + 1)
    return unpack("b", ram.read(1))[0]

def get_anim_entry(ram: PspRamIO, mdl_id: int, wpn_type: int) -> dict[str, int]:
    entry = {
        "mdl_count": 0,
        "tex_count": 0,
        "mdl_add": 0,
        "tex_add": 0
    }
    ram.seek(ANIM_LOAD)
    while (buf := ram.read(4)) != b'\xFF\xFF\xFF\xFF':
        if (wpn_type-5, mdl_id) == unpack('<HBx', buf):
            ram.seek(-4, 1)
            print("Found it!")
            entry["mdl_count"], entry["tex_count"], entry["mdl_add"], entry["tex_add"] = unpack("<3x2B3x2I4x", ram.read(20))
            break
        else:
            ram.seek(0x10, 1)
    return entry


class Anim(Frame):
    def __init__(self, master, a_type: AnimType, a_id: str, keyframes: list[int], bone: int):
        super().__init__(master)
        self.anim_type: AnimType = a_type
        self.anim_id: str = a_id
        self.bone: IntVar = IntVar()
        self.frame_vars: list[IntVar] = [IntVar() for _ in range(6)]
        self.showing_frames: bool = False
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        for x in range(6):
            self.frame_vars[x].set(keyframes[x])
        self.bone.set(bone)

        self.info = Label(self, text=f'{self.anim_id}')
        self.bone_label = Label(self, text="BONE: " if a_type is AnimType.Vertex else "OBJ: ")
        self.bone_entry = Entry(self, textvariable=self.bone, width=2)

        self.frame_entries: Frame = Frame(self)
        for i in range(6):
            Scale(self.frame_entries, from_=ANIM_TYPE_RANGES[a_type.value][a_id][0], to=ANIM_TYPE_RANGES[a_type.value][a_id][1], variable=self.frame_vars[i]).grid(row=i, column=1, sticky="WE")
            Label(self.frame_entries, textvariable=self.frame_vars[i], width=5).grid(row=i, column=0, sticky="WE")

        self.toggle_button = Button(self, text="↓", command=self.toggle)
        
        self.info.grid(row=0, column=0, sticky="WE")
        self.bone_label.grid(row=0, column=1, sticky="WE")
        self.bone_entry.grid(row=0, column=2, sticky="WE")
        self.toggle_button.grid(row=3, column=0, columnspan=3, sticky="WE")
    
    def snap_scales(self) -> None:
        [x.set(x.get()) for x in self.frame_vars]
    
    def toggle(self) -> None:
        if self.showing_frames:
            self.toggle_button.config(text="↓")
            self.frame_entries.grid_forget()
        else:
            self.frame_entries.grid(row=2, column=0, columnspan=3, sticky="WE")
            self.toggle_button.config(text="↑")
        
        self.showing_frames = not self.showing_frames
    
    @property
    def frames(self) -> list[int]:
        self.snap_scales()
        return [x.get() for x in self.frame_vars]
    
    def get_anim_data(self) -> dict[str, Any]:
        return {
            "id": self.anim_id,
            "type": self.anim_type,
            "keyframes": self.frames,
            "bone": self.bone.get()
        }
    
    def get_anim(self) -> bytes:
        return pack("<2BxB6i", ANIM_TYPES["MODEL" if self.anim_type is AnimType.Vertex else "TEXTURE"][self.anim_id], self.bone.get(), 3, *self.frames)


class App(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.running = False
        self.title("WPN ANIM RTE")
        self.minsize(200, 100)
        self.ram: PspRamIO
        self.animations: list[Anim] = []

        self.init_button = Button(self, text="Start", command=self.init)
        self.instruct_text = Label(self, text="Load MHP3rd (ULJM05800) in PPSSPP,\nequip a modded weapon using\ncustom animations and press 'Start'.", anchor="center", justify="center")
        self.instruct_text.pack()
        self.init_button.pack()
    
    def destroy(self):
        try:
            self.ram.close()
        except:
            pass
        self.running = False
        return super().destroy()
    
    def init(self) -> None:
        self.ram = PspRamIO()
        self.init_button.pack_forget()
        self.instruct_text.pack_forget()
        get_animations(self, self.ram)
        Button(self, text="Update", command=self.inject).pack(fill=X, expand=True)
        Button(self, text="Get Json", command=self.gen_json).pack(fill=X, expand=True)
    
    def inject(self) -> None:
        mdl_id = get_model_id(self.ram)
        wpn_type = get_weapon_type(self.ram)
        entry = get_anim_entry(self.ram, mdl_id, wpn_type)

        anim_idx = 0

        self.ram.seek(entry["mdl_add"])
        for _ in range(entry["mdl_count"]):
            self.ram.write(self.animations[anim_idx].get_anim())
            anim_idx += 1
        self.ram.seek(entry["tex_add"])
        for _ in range(entry["tex_count"]):
            self.ram.write(self.animations[anim_idx].get_anim())
            anim_idx += 1
    
    def gen_json(self) -> None:
        data = {
            "type": WPN_TYPES[get_weapon_type(self.ram) - 5],
            "model": [],
            "texture": []
        }
        for anim in map(lambda x: x.get_anim_data(), self.animations):
            data["model" if anim["type"] is AnimType.Vertex else "texture"].append({
                "type": anim["id"],
                "bone": anim["bone"],
                "keyframes": anim["keyframes"]
            })
        
        top = Toplevel(self)
        top.title("Json Code")
        txt_box = Text(top)
        txt_box.delete("1.0", END)
        txt_box.insert("1.0", dumps(data, indent=2))
        txt_box.pack()
    
    def run(self) -> None:
        self.running = True
        while self.running:
            self.update()


def get_animations(root: App, ram: PspRamIO) -> None:
    mdl_id = get_model_id(ram)
    wpn_type = get_weapon_type(ram)
    entry = get_anim_entry(ram, mdl_id, wpn_type)
    
    Label(root, text="Model", anchor="center", background="lightgrey").pack(fill=X, expand=True)

    ram.seek(entry["mdl_add"])
    for _ in range(entry["mdl_count"]):
        anim_info = unpack('2Bxx6I', ram.read(0x1C))
        anim = Anim(master=root,
            a_type=AnimType.Vertex,
            a_id=R_ANIM_TYPES["MODEL"][anim_info[0]],
            keyframes=list(anim_info[-6:]),
            bone=anim_info[1]
        )
        root.animations.append(anim)
        root.animations[-1].pack(fill=X, expand=True)

    Separator(root, orient="horizontal").pack(fill=X, expand=True)
    
    Label(root, text="Texture", anchor="center", background="lightgrey").pack(fill=X, expand=True)

    ram.seek(entry["tex_add"])
    for _ in range(entry["tex_count"]):
        anim_info = unpack('2Bxx6I', ram.read(0x1C))
        anim = Anim(master=root,
            a_type=AnimType.Texture,
            a_id=R_ANIM_TYPES["TEXTURE"][anim_info[0]],
            keyframes=list(anim_info[-6:]),
            bone=anim_info[1]
        )
        root.animations.append(anim)
        root.animations[-1].pack(fill=X, expand=True)
    
    Separator(root, orient="horizontal").pack(fill=X, expand=True)



if __name__ == "__main__":
    a = App()
    a.run()
