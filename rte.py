"""

Anim Entry Format:

    short WeaponType;
    byte ModelID;
    byte ModelAnimCount;
    byte TexAnimCount;
    byte UnkAnimCount;
    byte RestingPosition;
    byte padding;
    int ModelAnimAdd;
    int TexAnimAdd;
    int UnkAnimAdd;

"""

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
CUSTOM_ANIM_LOAD    = 0x099C0000
ANIM_LOAD           = 0x089ed9dc
TEST_TEX_ADD        = 0x099C0200
TEST_MDL_ADD        = 0x099C0100

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
        "H_STRIDE": (-128, 128),
        "V_STRIDE": (-128, 128),
        "LUMA (SMOOTH)": (0, 255),
        "LUMA": (0, 255),
        "VISIBLE(WEIRD)": (0, 255),
        "ALPHA": (0, 255),
        "COLOR": (0, 255),
        "RGB": (0, 1),
        "VISIBLE": (0, 1)
    },
    "Vertex": {
        "ROTATE_X": (-300, 300),
        "ROTATE_Y": (-300, 300),
        "ROTATE_Z": (-300, 300),
        "ROTATION_X": (0, 4),
        "ROTATION_Y": (0, 4),
        "ROTATION_Z": (0, 4),
        "SCALE": (0, 300),
        "SCALE_XY": (0, 300),
        "SCALE_XZ": (0, 300),
        "SCALE_YZ": (0, 300),
        "SCALE_Z": (0, 300),
        "TRANSLATE_Y": (-300, 300),
        "TRANSLATE_X": (-300, 300),
        "TRANSLATE_Z": (-300, 300),
        "RECITAL": (-10, 10)
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
        "unk_count": 0,
        "mdl_add": 0,
        "tex_add": 0,
        "unk_add": 0,
        "resting_pos": 0,
    }
    ram.seek(ANIM_LOAD)
    while (buf := ram.read(4))[:2] != b'\xFF\xFF':
        if (wpn_type-5, mdl_id) == unpack('<HBx', buf):
            ram.seek(-4, 1)
            print(f"Found it!: {hex(ram.tell())}")
            entry["mdl_count"], entry["tex_count"], entry["unk_count"], entry["resting_pos"], entry["mdl_add"], entry["tex_add"], entry["unk_add"] = unpack("<3x4Bx3I", ram.read(20))
            break
        else:
            ram.seek(0x10, 1)
    ram.seek(CUSTOM_ANIM_LOAD)
    while (buf := ram.read(4))[:2] != b'\xFF\xFF':
        if (wpn_type-5, mdl_id) == unpack('<HBx', buf):
            ram.seek(-4, 1)
            print(f"Found it!: {hex(ram.tell())}")
            entry["mdl_count"], entry["tex_count"], entry["unk_count"], entry["resting_pos"], entry["mdl_add"], entry["tex_add"], entry["unk_add"] = unpack("<3x4Bx3I", ram.read(20))
            return entry
        else:
            ram.seek(0x10, 1)
    return entry

def overwrite_entry(ram: PspRamIO, mdl_id: int, wpn_type: int, mdl_count: int, tex_count: int, mdl_addr: int, tex_addr: int, resting_pos: int):
    ram.seek(ANIM_LOAD)
    entry_add = 0
    while (buf := ram.read(4))[:2] != b'\xFF\xFF':
        if (wpn_type-5, mdl_id) == unpack('<HBx', buf):
            ram.seek(-1, 1)
            print("Found it!")
            entry_add = ram.tell()
            break
        else:
            ram.seek(0x10, 1)
    ram.seek(CUSTOM_ANIM_LOAD)
    while (buf := ram.read(4))[:2] != b'\xFF\xFF':
        if (wpn_type-5, mdl_id) == unpack('<HBx', buf):
            ram.seek(-1, 1)
            print("Found it!")
            entry_add = ram.tell()
            break
        else:
            ram.seek(0x10, 1)
    if entry_add != 0:
        ram.seek(entry_add)
        ram.write(pack("<2B", mdl_count, tex_count))
        ram.seek(1, 1)
        ram.write(pack("<B", resting_pos))
        ram.seek(1, 1)
        ram.write(pack("<2I", mdl_addr, tex_addr))

class Anim(Frame):
    def __init__(self, app, master, a_type: AnimType, a_id: str, keyframes: list[int], bone: int):
        super().__init__(master)
        self.anim_type: AnimType = a_type
        self.anim_id: StringVar = StringVar()
        self.bone: IntVar = IntVar()
        self.frame_vars: list[IntVar] = [IntVar() for _ in range(6)]
        self.showing_frames: bool = False
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        for x in range(6):
            self.frame_vars[x].set(keyframes[x])
        self.bone.set(bone)

        self.info = OptionMenu(self, self.anim_id, list(ANIM_TYPES["MODEL" if a_type is AnimType.Vertex else "TEXTURE"].keys())[0], *ANIM_TYPES["MODEL" if a_type is AnimType.Vertex else "TEXTURE"].keys(), command=self.update_scales)

        self.anim_id.set(a_id)

        self.bone_label = Label(self, text="BONE: " if a_type is AnimType.Vertex else "OBJ: ")
        self.bone_entry = Entry(self, textvariable=self.bone, width=2)

        self.frame_entries: Frame = Frame(self)
        self.frame_entries.columnconfigure(0, weight=1)
        self.frame_entries.columnconfigure(1, weight=2)
        self.frame_entries.columnconfigure(2, weight=1)
        self.scales = []
        for i in range(6):
            self.scales.append(Scale(self.frame_entries, from_=ANIM_TYPE_RANGES[a_type.value][a_id][0], to=ANIM_TYPE_RANGES[a_type.value][a_id][1], variable=self.frame_vars[i]))
            self.scales[-1].grid(row=i, column=1, sticky="WE")
            Label(self.frame_entries, textvariable=self.frame_vars[i], width=5).grid(row=i, column=0, sticky="WE")
        
        Button(self.frame_entries, text="↑", width=1, command=lambda : app.move_up(self)).grid(row=6, column=0, sticky="WE")
        Button(self.frame_entries, text="Delete", style="Delete.TButton", command=lambda : app.remove_anim(self)).grid(row=6, column=1, columnspan=1, sticky="WE")
        Button(self.frame_entries, text="↓", width=1, command=lambda : app.move_down(self)).grid(row=6, column=2, sticky="WE")

        self.toggle_button = Button(self, text="Expand", command=self.toggle)
        
        self.info.grid(row=0, column=0, sticky="WE")
        self.bone_label.grid(row=0, column=1, sticky="WE")
        self.bone_entry.grid(row=0, column=2, sticky="WE")
        self.toggle_button.grid(row=3, column=0, columnspan=3, sticky="WE")
    
    def update_scales(self, e) -> None:
        for scale in self.scales:
            scale.config(from_=ANIM_TYPE_RANGES[self.anim_type.value][self.anim_id.get()][0], to=ANIM_TYPE_RANGES[self.anim_type.value][self.anim_id.get()][1])

    def snap_scales(self) -> None:
        [x.set(x.get()) for x in self.frame_vars]
    
    def toggle(self) -> None:
        if self.showing_frames:
            self.toggle_button.config(text="Expand")
            self.frame_entries.grid_forget()
        else:
            self.frame_entries.grid(row=2, column=0, columnspan=3, sticky="WE")
            self.toggle_button.config(text="Collapse")
        
        self.showing_frames = not self.showing_frames
    
    @property
    def frames(self) -> list[int]:
        self.snap_scales()
        return [x.get() for x in self.frame_vars]
    
    def get_anim_data(self) -> dict[str, Any]:
        return {
            "id": self.anim_id.get(),
            "type": self.anim_type,
            "keyframes": self.frames,
            "bone": self.bone.get()
        }
    
    def get_anim(self) -> bytes:
        return pack("<2BxB6i", ANIM_TYPES["MODEL" if self.anim_type is AnimType.Vertex else "TEXTURE"][self.anim_id.get()], self.bone.get(), 3, *self.frames)

class App(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.running = False
        self.title("WPN ANIM RTE")
        self.minsize(200, 100)
        self.ram: PspRamIO
        self.mdl_animations: list[Anim] = []
        self.tex_animations: list[Anim] = []
        self.resting_pos: IntVar = IntVar()
        self.resting_pos.set(0)

        self.mdl_frame: Frame = Frame(self)
        self.tex_frame: Frame = Frame(self)

        self.init_button = Button(self, text="Start", command=self.init)
        self.instruct_text = Label(self, text="Load MHP3rd (ULJM05800) in PPSSPP,\nequip a weapon that uses custom\nanimations and press 'Start'.", anchor="center", justify="center")
        self.instruct_text.pack()
        self.init_button.pack()

        style = Style(self)
        style.map("Delete.TButton",
            foreground=[('!active', 'black'),('pressed', 'red'), ('active', 'red')],
            background=[ ('!active','grey75'),('pressed', 'red'), ('active', 'red')]
        )

        
    
    def destroy(self):
        try:
            self.ram.close()
        except:
            pass
        self.running = False
        return super().destroy()
    
    @property
    def animations(self) -> list:
        return self.mdl_animations + self.tex_animations

    def update_mdl_list(self, idx: int = 0) -> None:
        for x in self.mdl_animations[idx:]:
            x.pack_forget()
            x.pack(fill=X, expand=True)
    
    def update_tex_list(self, idx: int = 0) -> None:
        for x in self.tex_animations[idx:]:
            x.pack_forget()
            x.pack(fill=X, expand=True)

    def move_up(self, anim: Anim) -> None:
        if anim.anim_type is AnimType.Vertex:
            idx = self.mdl_animations.index(anim)
            if idx == 0:
                return
            self.mdl_animations[idx - 1], self.mdl_animations[idx] = self.mdl_animations[idx], self.mdl_animations[idx - 1]
            self.update_mdl_list(idx=idx-1)
        else:
            idx = self.tex_animations.index(anim)
            if idx == 0:
                return
            self.tex_animations[idx - 1], self.tex_animations[idx] = self.tex_animations[idx], self.tex_animations[idx - 1]
            self.update_tex_list(idx=idx-1)
    
    def move_down(self, anim: Anim) -> None:
        if anim.anim_type is AnimType.Vertex:
            idx = self.mdl_animations.index(anim)
            if idx == len(self.mdl_animations)-1:
                return
            self.mdl_animations[idx + 1], self.mdl_animations[idx] = self.mdl_animations[idx], self.mdl_animations[idx + 1]
            self.update_mdl_list(idx=idx)
        else:
            idx = self.tex_animations.index(anim)
            if idx == len(self.tex_animations)-1:
                return
            self.tex_animations[idx + 1], self.tex_animations[idx] = self.tex_animations[idx], self.tex_animations[idx + 1]
            self.update_tex_list(idx=idx)

    def remove_anim(self, anim: Anim) -> None:
        if anim.anim_type is AnimType.Vertex:
            idx = self.mdl_animations.index(anim)
            self.mdl_animations[idx].pack_forget()
            del self.mdl_animations[idx]
        else:
            idx = self.tex_animations.index(anim)
            self.tex_animations[idx].pack_forget()
            del self.tex_animations[idx]
    
    def add_tex(self) -> None:
        self.tex_animations.append(Anim(app=self,
            master=self.tex_frame,
            a_type=AnimType.Texture,
            a_id="H_STRIDE",
            keyframes=[0]*6,
            bone=0
        ))
        self.tex_animations[-1].pack(fill=X, expand=True)
    
    def add_mdl(self) -> None:
        self.mdl_animations.append(Anim(app=self,
            master=self.mdl_frame,
            a_type=AnimType.Vertex,
            a_id="ROTATE_X",
            keyframes=[0]*6,
            bone=0
        ))
        self.mdl_animations[-1].pack(fill=X, expand=True)

    def init(self) -> None:
        self.init_button.pack_forget()
        Label(self, text="Resting Position", anchor="center", background="lightgrey").pack(fill=X, expand=True)
        LabeledScale(self, from_=0, to=69, variable=self.resting_pos).pack(fill=X, expand=True)
        self.instruct_text.pack_forget()
        Label(self, text="Model", anchor="center", background="lightgrey").pack(fill=X, expand=True)
        self.mdl_frame.pack(fill=X, expand=True)
        Button(self, text="Add", command=self.add_mdl).pack(fill=X, expand=True)
        Separator(self, orient="horizontal").pack(fill=X, expand=True)
        Label(self, text="Texture", anchor="center", background="lightgrey").pack(fill=X, expand=True)
        self.tex_frame.pack(fill=X, expand=True)
        Button(self, text="Add", command=self.add_tex).pack(fill=X, expand=True)
        Separator(self, orient="horizontal").pack(fill=X, expand=True)
        Button(self, text="Update", command=self.inject).pack(fill=X, expand=True)
        Button(self, text="Get Json", command=self.gen_json).pack(fill=X, expand=True)

        self.ram = PspRamIO()
        get_animations(self, self.ram)
    
    def inject(self) -> None:
        mdl_id = get_model_id(self.ram)
        wpn_type = get_weapon_type(self.ram)
        overwrite_entry(self.ram, mdl_id, wpn_type, len(self.mdl_animations), len(self.tex_animations), TEST_MDL_ADD, TEST_TEX_ADD, self.resting_pos.get())

        self.ram.seek(TEST_MDL_ADD)
        for anim in self.mdl_animations:
            self.ram.write(anim.get_anim())
        self.ram.seek(TEST_TEX_ADD)
        for anim in self.tex_animations:
            self.ram.write(anim.get_anim())
    
    def gen_json(self) -> None:
        data = {
            "type": WPN_TYPES[get_weapon_type(self.ram) - 5],
            "resting_pos": self.resting_pos.get(),
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

    ram.seek(entry["mdl_add"])
    for _ in range(entry["mdl_count"]):
        anim_info = unpack('2Bxx6i', ram.read(0x1C))
        anim = Anim(app=root,
            master=root.mdl_frame,
            a_type=AnimType.Vertex,
            a_id=R_ANIM_TYPES["MODEL"][anim_info[0]],
            keyframes=list(anim_info[-6:]),
            bone=anim_info[1]
        )
        root.mdl_animations.append(anim)
        root.mdl_animations[-1].pack(fill=X, expand=True)

    ram.seek(entry["tex_add"])
    for _ in range(entry["tex_count"]):
        anim_info = unpack('2Bxx6I', ram.read(0x1C))
        anim = Anim(app=root,
            master=root.tex_frame,
            a_type=AnimType.Texture,
            a_id=R_ANIM_TYPES["TEXTURE"][anim_info[0]],
            keyframes=list(anim_info[-6:]),
            bone=anim_info[1]
        )
        root.tex_animations.append(anim)
        root.tex_animations[-1].pack(fill=X, expand=True)



if __name__ == "__main__":
    a = App()
    a.run()
