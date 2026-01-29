from utils import *
import pymem
import os

ds3 = pymem.Pymem("DarkSoulsIII.exe")
module = pymem.process.module_from_name(ds3.process_handle, "DarkSoulsIII.exe")

# These are all pointers. Saved in memory to reduce recomputing.
world_chr_man = get_world_chr_man(ds3, module)
player_stats = follow_chain(ds3, world_chr_man, [0x80, 0x1F90, 0x18])
player_curr_hp = player_stats + 0xD8
player_max_hp = player_stats + 0xDC
player_curr_sp = player_stats + 0xF0
player_max_sp = player_stats + 0xF4

print("--------- Game Info ----------")
print(f'Player Current HP: {ds3.read_int(player_curr_hp)}')
print(f'Player Max HP: {ds3.read_int(player_max_hp)}')
print(f'Player Current SP: {ds3.read_int(player_curr_sp)}')
print(f'Player Max SP: {ds3.read_int(player_max_sp)}')

iudex_gundyr = get_entity(ds3, world_chr_man, IUDEX_GUNDYR)
iudex_curr_hp = iudex_gundyr + 0xD8
iudex_max_hp = iudex_gundyr + 0xDC

os.system("cls" if os.name == "nt" else "clear")
print("\033[?25l", end="")
while True:
    print("\033[H", end="")
    
    print("----- Game Info ------")
    print(f'Player Current HP: {ds3.read_int(player_curr_hp)}')
    print(f'Player Max HP: {ds3.read_int(player_max_hp)}')
    
    # Neccessary to avoid weird visual bug when SP becomes negative
    print("\033[K", end="")
    print(f'Player Current SP: {ds3.read_int(player_curr_sp)}')

    print(f'Player Max SP: {ds3.read_int(player_max_sp)}')
    print()
    print(f'Boss Current HP: {ds3.read_int(iudex_curr_hp)}')
    print(f'Boss Max HP: {ds3.read_int(iudex_max_hp)}')
