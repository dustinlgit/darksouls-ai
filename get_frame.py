import mss
import numpy as np
import cv2
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
import win32gui
import time
import pymem
import ds3_open as open

def get_one_frame_fullscreen():
    '''takes 1 ss of the game in fullscreen mode. must change to the right monitor & the game to capture the screen'''
    with mss.mss() as sct:
        monitor = sct.monitors[2]
        frame = np.array(sct.grab(monitor))[:, :, :3]
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (128, 128), interpolation=cv2.INTER_AREA)
    cv2.imwrite("ds3_frame.png", frame)
    print("Saved ds3_frame.png")

def get_ds_window():
    hwnd = win32gui.FindWindow(None, "DARK SOULS III")
    if hwnd:
        return hwnd
    else:
        print("Dark Souls Window not Found.")

def get_one_frame(ds3Reader, timeout=20.0, poll=0.5):
    '''gets 1 ss of the game in windowed mode, returns frame as numpy array'''
    t0 = time.time()
    last_launch = 0

    def blank():
        return np.zeros((128, 128, 1), dtype=np.uint8)

    while time.time() - t0 < timeout:
        hwnd = get_ds_window()

        if hwnd and win32gui.IsWindow(hwnd):
            try:
                left, top, right, bottom = win32gui.GetClientRect(hwnd)
                screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
                screen_right, screen_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
                w = screen_right - screen_left
                h = screen_bottom - screen_top
                if w <= 0 or h <= 0:
                    time.sleep(poll)
                    continue

                with mss.mss() as sct:
                    monitor = {"left": screen_left, "top": screen_top, "width": w, "height": h}
                    frame = np.array(sct.grab(monitor))[:, :, :3]

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.resize(frame, (128, 128), interpolation=cv2.INTER_AREA)
                return frame.reshape(128, 128, 1).astype(np.uint8)
            except Exception:
                time.sleep(poll)
                continue

        # No window: relaunch only if process is not running (with cooldown)
        if not open._ds3_running():
            now = time.time()
            if now - last_launch > 15:
                print("DS3 not running -> launching from get_frame...")
                open.enter_game()
                last_launch = now
                time.sleep(5)

        time.sleep(poll)

    return blank()



# if __name__ == "__main__":
#     while True:
#         frame = get_one_frame()
#         if frame is not None:
#             cv2.imwrite("ds3_frame.png", frame)
#             print("Saved ds3_frame.png")
#         time.sleep(0.5)

