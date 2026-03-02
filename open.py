import subprocess
from pathlib import Path
import pydirectinput as pdi
import time
import traceback
import win32gui
import win32con
import time
import time
import psutil
import subprocess
from pathlib import Path
import win32gui

DS3_EXE = "DarkSoulsIII.exe"

# Add/remove names based on what you actually see in Task Manager
KILL_THESE = {
    "darksoulsiii.exe",
    "me3_launcher.exe",     # if it exists
    "me3_mod_host.exe",     # if it exists
    "me3.exe",              # if it exists
    "me3_launcher.exe",
    "me3_mod_host.exe",
    "me3.exe"
}

def _kill_by_name(names, timeout=8.0):
    names = {n.lower() for n in names}
    procs = []
    for p in psutil.process_iter(["pid", "name"]):
        name = (p.info["name"] or "").lower()
        if name in names:
            procs.append(p)

    for p in procs:
        try: p.terminate()
        except Exception: pass

    t0 = time.time()
    while time.time() - t0 < timeout:
        alive = []
        for p in procs:
            try:
                if p.is_running():
                    alive.append(p)
            except Exception:
                pass
        if not alive:
            return
        time.sleep(0.2)

    for p in procs:
        try:
            if p.is_running():
                p.kill()
        except Exception:
            pass

def focus_window(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        print("Could not focus window")
        return
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    return hwnd

def _ds3_running():
    for p in psutil.process_iter(["name"]):
        if (p.info["name"] or "").lower() == DS3_EXE.lower():
            focus_window("DARK SOULS III")
            return True
    return False

def enter_game(timeout=90.0):
    """
    Pure relaunch:
      - kills leftover DS3 / mod host processes
      - runs launch.bat
      - waits until DarkSoulsIII.exe exists
    Does NOT click anything and does NOT search windows.
    """
    launchbat_path = Path(r"C:\Users\leahs\Downloads\Boss Arena (Sandbox Mode)-1854-Sandbox-2-3-1758292375\Dark Souls 3 Boss Arena (Sandbox 2.3)\launch.bat")

    # 1) close previous shit
    _kill_by_name(KILL_THESE)

    # 2) start launcher
    subprocess.Popen(["cmd", "/c", str(launchbat_path)], cwd=str(launchbat_path.parent), stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW)

    # 3) wait for DS3 process
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _ds3_running():
            time.sleep(15)
            pdi.click(960, 540) 
            time.sleep(0.2)

            print("trying to right click")

            pdi.mouseDown(button="right")
            time.sleep(0.05)
            pdi.mouseUp(button="right")
            time.sleep(3)

            pdi.click(968, 706)
            time.sleep(0.5)

            print("trying to left click okay")

            pdi.mouseDown(button="left")
            time.sleep(0.2)
            pdi.mouseUp(button="left")
            pdi.mouseDown(button="left")
            time.sleep(0.2)
            pdi.mouseUp(button="left")
            pdi.mouseDown(button="left")
            time.sleep(0.2)
            pdi.mouseUp(button="left")
            time.sleep(3)

            pdi.click(970, 780)
            time.sleep(0.2)

            print("trying to left click continue")

            pdi.mouseDown(button="left")
            time.sleep(0.2)
            pdi.mouseUp(button="left")
            pdi.mouseDown(button="left")
            time.sleep(0.2)
            pdi.mouseUp(button="left")
            time.sleep(3)


            print("stopped trying")
            return True
        time.sleep(0.25)

    return False