import vgamepad as vg
import time
import win32gui
import win32con

def keep_ds3_alive():
    hwnd = win32gui.FindWindow(None, "DARK SOULS III")
    if hwnd:
        # SW_SHOWNOACTIVATE displays the window in its current size and position 
        # but does NOT take focus away from your current typing/work.
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)

# Initialize the virtual gamepad
gamepad = vg.VX360Gamepad()

def release_all_keys():
    """Reset gamepad state to neutral"""
    gamepad.reset()
    gamepad.update()

def right_hand_light_attack():
    # RB on Xbox
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()
    time.sleep(0.1)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()

def forward_run_attack():
    # Tilt stick forward + RB
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)
    gamepad.update()
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()
    time.sleep(0.1)
    gamepad.reset()
    gamepad.update()

def dodge():
    # Tap B
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(0.05)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()

def forward_roll_dodge():
    # Forward + B
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(0.05)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()

def run_forward(sec):
    # Forward + Hold B
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec)
    gamepad.reset()
    gamepad.update()

def run_back(sec):
    # Forward + Hold B
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=-1.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec)
    gamepad.reset()
    gamepad.update()

def run_right(sec):
    # Forward + Hold B
    gamepad.left_joystick_float(x_value_float=1.0, y_value_float=0.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec)
    gamepad.reset()
    gamepad.update()

def run_left(sec):
    # Forward + Hold B
    gamepad.left_joystick_float(x_value_float=-1.0, y_value_float=0.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec)
    gamepad.reset()
    gamepad.update()

def walk_to_boss():
    release_all_keys()
    # Run forward
    run_forward(1.0)
    # Interact (A Button)
    for _ in range(2):
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.1)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0)
    
    run_forward(5.0)
    # Lock on (RS Click)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()
    time.sleep(0.1)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()

def boss_died_reset():
    release_all_keys()
    for _ in range(4):
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.1)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0)
