import mss
import numpy as np
import cv2
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
import win32gui
import time

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

def get_one_frame():
    '''gets 1 ss of the game in windowed mode, returns frame as numpy array'''
    hwnd = get_ds_window()
    if not hwnd:
        print("Dark Souls not Found, could not get frame")
        return None
    
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
    screen_right, screen_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
    w = screen_right - screen_left
    h = screen_bottom - screen_top

    with mss.mss() as sct:
        monitor = {
            "left": screen_left,
            "top": screen_top,
            "width": w,
            "height": h
        }
        frame = np.array(sct.grab(monitor))[:, :, :3]

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (128, 128), interpolation=cv2.INTER_AREA) 
    frame = frame.reshape(128, 128, 1)

    return frame

if __name__ == "__main__":
    while True:
        frame = get_one_frame()
        if frame is not None:
            cv2.imwrite("ds3_frame.png", frame)
            print("Saved ds3_frame.png")
        time.sleep(0.5)

