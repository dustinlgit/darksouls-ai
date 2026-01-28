import pymem
import os

def follow_chain(addr, offsets):
    ptr = addr
    for offset in offsets:
        ptr = ds3.read_longlong(ptr + offset)
        print(hex(ptr))
    return ptr

ds3 = pymem.Pymem("DarkSoulsIII.exe")
module = pymem.process.module_from_name(ds3.process_handle, "DarkSoulsIII.exe")
base = module.lpBaseOfDll

pattern = b"\x48\x8B\x1D...\x04\x48\x8B\xF9\x48\x85\xDB..\x8B\x11\x85\xD2..\x8D"

instr = pymem.pattern.pattern_scan_module(
    ds3.process_handle,
    module,
    pattern,
    return_multiple=False
)

offset = ds3.read_int(instr + 3)

WorldChrManAddr = instr + 7 + offset
WorldChrMan = ds3.read_longlong(WorldChrManAddr)

PlayerStats = follow_chain(WorldChrMan, [0x80, 0x1F90, 0x18])
HP = PlayerStats + 0xD8
MaxHP = PlayerStats + 0xDC
SP = PlayerStats + 0xF0
MaxSP = PlayerStats + 0xF4

while True:
    os.system("cls" if os.name == "nt" else "clear")
    
    print("--------- Game Info ----------")
    print(f'Player Current HP: {ds3.read_int(HP)}')
    print(f'Player Max HP: {ds3.read_int(MaxHP)}')
    print(f'Player Current SP: {ds3.read_int(SP)}')
    print(f'Player Max SP: {ds3.read_int(MaxSP)}')


