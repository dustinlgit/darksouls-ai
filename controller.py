import vgamepad as vg
import time
import win32gui
import win32con

gamepad = vg.VX360Gamepad()

STICK_VALUE = 0.8
PRESS_DURATION = 1 / 60

# --- Movement ---
def no_action():
    time.sleep(PRESS_DURATION)

def move_neutral():
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
    gamepad.update()

def move_forward():
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=STICK_VALUE)
    gamepad.update()

def move_back():
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=-STICK_VALUE)
    gamepad.update()

def move_left():
    gamepad.left_joystick_float(x_value_float=-STICK_VALUE, y_value_float=0.0)
    gamepad.update()

def move_right():
    gamepad.left_joystick_float(x_value_float=STICK_VALUE, y_value_float=0.0)
    gamepad.update()

def attack():
    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()
    time.sleep(PRESS_DURATION)
    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()

def dodge():
    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(PRESS_DURATION)
    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()

def heal():
    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    gamepad.update()
    time.sleep(PRESS_DURATION)
    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    gamepad.update()

def lock_on():
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()

    time.sleep(PRESS_DURATION) 

    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()


def turn_lock_on(min_deg=90, max_deg=180):
    gamepad.right_joystick(x_value=32767, y_value=0)
    gamepad.update()

    time.sleep(PRESS_DURATION)

    gamepad.right_joystick(x_value=0, y_value=0)
    gamepad.update()

    lock_on()

    
def keep_ds3_alive():
    hwnd = win32gui.FindWindow(None, "DARK SOULS III")
    if hwnd:
        # SW_SHOWNOACTIVATE displays the window in its current size and position 
        # but does NOT take focus away from your current typing/work.
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)

def release_all():
    gamepad.reset()
    gamepad.update()


def walk_to_boss(speed):
    release_all()
    # Run forward
    move_forward()
    time.sleep(1.5 / speed)
    gamepad.reset()
    gamepad.update()
    for _ in range(4):
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.1 / speed)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0 / speed)
    
    move_forward()
    time.sleep(6.25 / speed)
    gamepad.reset()
    gamepad.update()
    # Lock on (RS Click)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()
    time.sleep(0.1 / speed)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()

def boss_died_reset():
    release_all()
    for _ in range(4):
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.1)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0)

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