import mss
import numpy as np
import cv2
import time
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
import win32gui

def get_one_frame_fullscreen():
    '''takes 1 ss of the game in fullscreen mode. must change to the right monitor & the game to capture the screen'''
    scale_factor = 0.5
    with mss.mss() as sct:
        monitor = sct.monitors[2]
        frame = np.array(sct.grab(monitor))[:, :, :3]
    frame = cv2.resize(frame, (400, 400), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA) #can change size 400x400, if needed
    cv2.imwrite("ds3_frame.png", frame)
    print("Saved ds3_frame.png")

def get_ds_window():
    hwnd = win32gui.FindWindow(None, "DARK SOULS III")
    
    if hwnd:
        print("Dark Souls Found.")
        return hwnd
    else:
        print("Dark Souls not Found.")

def get_one_frame():
    '''gets 1 ss of the game in windowed mode'''
    hwnd = get_ds_window()
    if not hwnd:
        print("Dark Souls not Found, could not get frame")
        return
    
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    screen_left, screen_top = win32gui.ClientToScreen(hwnd, (left, top))
    screen_right, screen_bottom = win32gui.ClientToScreen(hwnd, (right, bottom))
    w = screen_right - screen_left
    h = screen_bottom - screen_top
    scale_factor = 0.5

    with mss.mss() as sct:
        monitor = {
            "left": screen_left,
            "top": screen_top,
            "width": w,
            "height": h
        }
        frame = np.array(sct.grab(monitor))[:, :, :3]
    frame = cv2.resize(frame, (400, 400), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA) #can change size 400x400, if needed
    cv2.imwrite("ds3_frame.png", frame)
    print("Saved ds3_frame.png")

while True:
    get_one_frame()
    time.sleep(0.5)

