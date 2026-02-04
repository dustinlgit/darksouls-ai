import pymem


IUDEX_GUNDYR = 1037
BOSSES = [IUDEX_GUNDYR]

WORLD_CHR_MAN_PATTERN = b"\x48\x8B\x1D...\x04\x48\x8B\xF9\x48\x85\xDB..\x8B\x11\x85\xD2..\x8D"


def follow_chain(ds3, addr, offsets, debug=True):
    ptr = addr
    for offset in offsets:
        try:
            ptr = ds3.read_longlong(ptr + offset)

            if debug:
                print(hex(ptr))

        except Exception as e:
            print("Error handling memory offsets. Most likely harmless but a chain did fail.")

            if debug:
                print(e)

    return ptr


"""
Scans DS3 memory using AOB (Array of Bytes) to find WorldChrMan.
WorldChrMan is the root pointer in the pointer tree for almost all entities.
"""
def get_world_chr_man(ds3, module):
    pattern = b"\x48\x8B\x1D...\x04\x48\x8B\xF9\x48\x85\xDB..\x8B\x11\x85\xD2..\x8D"

    instr = pymem.pattern.pattern_scan_module(
        ds3.process_handle,
        module,
        pattern,
        return_multiple=False
    )
    offset = ds3.read_int(instr + 3)
    world_chr_man_addr = instr + 7 + offset

    return ds3.read_longlong(world_chr_man_addr)


"""
Currently checks using entity Max HP. 
Ideally would use NPCParam (ID), but can't figure out the offsets.
"""
def get_entity(ds3, world_chr_man, entity_max_hp):
    chr_num = ds3.read_int(ds3.read_longlong(world_chr_man + 0x1D0))
    chr_set = follow_chain(ds3, world_chr_man, [0x1D0, 0x8])
    entity = None
    
    print(chr_num)
    for i in range(chr_num):
        sprj_chr_data_module = follow_chain(ds3, chr_set, [i * 0x38, 0x1F90, 0x18])
        if ds3.read_int(sprj_chr_data_module + 0xDC) == entity_max_hp:
            entity = sprj_chr_data_module
    
    if entity is None: 
        raise ValueError(f'Entity with identifier [{entity_max_hp}] could not be found.')

    return entity
