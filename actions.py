import subprocess
from pathlib import Path
import pydirectinput as pdi
import time
from memory import utils
import pymem
import traceback
from memory import utils
import win32gui
import win32con
import time


def focus_window(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise RuntimeError("Window not found")
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    return hwnd

def ensure_ds3_focused(title="DARK SOULS III"):
    try:
        hwnd = win32gui.FindWindow(None, title)
        if not hwnd:
            return None
        if win32gui.GetForegroundWindow() != hwnd:
            focus_window(title)
        return hwnd
    except:
        print("Window check failed, but might just be on cd")

def release_all_keys():
    """Release all held keys to ensure clean state"""
    keys_to_release = ['w', 'a', 's', 'd', ' ', 'e', 'q', 'r', 'shift', 'ctrl']
    for key in keys_to_release:
        try:
            pdi.keyUp(key)
        except:
            pass
    # Release mouse buttons
    try:
        pdi.mouseUp(button='left')
        pdi.mouseUp(button='right')
    except:
        pass

def right_hand_light_attack():
    ensure_ds3_focused("DARK SOULS III")
    pdi.click()

def forward_run_attack():
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("w")
    pdi.keyUp("w")
    pdi.click()

def change_potion():
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown('down')
    pdi.keyUp('down')

def dodge():
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown(" ")
    pdi.keyUp(" ")

def forward_roll_dodge():
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("w")
    pdi.keyDown(" ")
    pdi.keyUp(" ")
    pdi.keyUp("w")

def shield(sec):
    ensure_ds3_focused("DARK SOULS III")
    pdi.mouseDown(button='right')
    time.sleep(sec)
    pdi.mouseUp(button='right')

def run_forward(sec):
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("w")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("w")
    pdi.keyUp(" ")

def run_back(sec):
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("s")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("s")
    pdi.keyUp(" ")


def run_right(sec):
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("d")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("d")
    pdi.keyUp(" ")


def run_left(sec):
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("a")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("a")
    pdi.keyUp(" ")

def heal():
    ensure_ds3_focused("DARK SOULS III")
    pdi.press("r")

def walk_to_boss():
    release_all_keys()
    ensure_ds3_focused("DARK SOULS III")
    run_forward(1)
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    run_forward(5)
    pdi.keyDown("q") #lock's camera on boss
    time.sleep(1)
    pdi.keyUp("q")

def boss_died_reset():
    ensure_ds3_focused("DARK SOULS III")
    release_all_keys()
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
    pdi.keyDown("e")
    time.sleep(1)
    pdi.keyUp("e")
def q_focus_boss():
    ensure_ds3_focused("DARK SOULS III")
    pdi.keyDown("q")
    time.sleep(0.8)
    pdi.keyUp("q")

def reset_game() -> tuple[bool, int]:
    '''returns (true, 0):Boss died, (true, 1):Player died, (false, 2):Neither died'''
    ds3 = pymem.Pymem("DarkSoulsIII.exe")
    module = pymem.process.module_from_name(ds3.process_handle, "DarkSoulsIII.exe")
    world_chr_man = utils.get_world_chr_man(ds3, module)
    iudex_gundyr = utils.get_entity(ds3, world_chr_man, utils.IUDEX_GUNDYR)
    player_stats = utils.follow_chain(ds3, world_chr_man, [0x80, 0x1F90, 0x18])
    player_curr_hp = player_stats + 0xD8
    iudex_curr_hp = iudex_gundyr + 0xD8
    iudex_max_hp = iudex_gundyr + 0xDC
    player_max_sp = player_stats + 0xF4
    player_curr_sp = player_stats + 0xF0
    player_max_hp = player_stats + 0xDC

    print("----- Game Info ------")
    print(f'Player Current HP: {ds3.read_int(player_curr_hp)}')
    print(f'Player Max HP: {ds3.read_int(player_max_hp)}')
    print(f'Player Current SP: {ds3.read_int(player_curr_sp)}')
    print(f'Player Max SP: {ds3.read_int(player_max_sp)}')
    print()
    print(f'Boss Current HP: {ds3.read_int(iudex_curr_hp)}')
    print(f'Boss Max HP: {ds3.read_int(iudex_max_hp)}')

    if ds3.read_int(iudex_curr_hp) == 0:
        print("Boss is dead")
        return (True, 0)
    elif ds3.read_int(player_curr_hp) == 0:
        print("Player is dead")
        return (True, 1)
    time.sleep(2)
    print("Neither died")
    return (False, 2)

def sim_game():
    '''continously runs game after player dies'''
    walk_to_boss()
    while True:
        reset, death_val = reset_game()
        if reset:
            if(death_val == 1): #player died
                time.sleep(15)
                walk_to_boss()
            elif(death_val == 0):
                time.sleep(15) 
                boss_died_reset() #will crash since cant read boss if we call reset_game right away
                time.sleep(10)
                walk_to_boss()
#sim_game()

(leah, jason, dustin) = (True, False, False) #CwwaHANGE! 
def enter_game():
    '''this actually launches the bat file for you and clicks any button to enter the game menu... 
            just an experiment we can add to if we want to use this logic'''
    leah_path = r"C:\Users\leahs\Downloads\Boss Arena (Sandbox Mode)-1854-Sandbox-2-3-1758292375\Dark Souls 3 Boss Arena (Sandbox 2.3)\launch.bat"
    jason_path = r""
    dustin_path = r""

    user_dict = {leah_path : leah, jason_path : jason, dustin_path : dustin}
    use_path = ""
    for user in user_dict:
        if(user_dict[user]):
            use_path = user

    launchbat_path = Path(use_path)
    subprocess.Popen(["cmd", "/c", str(launchbat_path)], cwd=str(launchbat_path.parent))
                    #run in cmd, then /c tells it to exit cmd after we launch path. 
                        #cwd => sandbox 2.3 folder
    time.sleep(15)
    pdi.click(960, 540) 
    time.sleep(0.2)

    print("trying to right click")

    pdi.mouseDown(button="right")
    time.sleep(0.05)
    pdi.mouseUp(button="right")
    time.sleep(3)

    print("stopped trying")
#enter_game()

