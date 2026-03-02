import vgamepad as vg
import time
import win32gui
import win32con
import open

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

    
def keep_ds3_alive():
    hwnd = win32gui.FindWindow(None, "DARK SOULS III")
    if hwnd:
        # SW_SHOWNOACTIVATE displays the window in its current size and position 
        # but does NOT take focus away from your current typing/work.
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
    else:
        print("keep_ds3_alive: re-entering the game, Window Not Found")
        open.enter_game()

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
    time.sleep(6.5 / speed)
    gamepad.reset()
    gamepad.update()
    # Lock on (RS Click)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()
    time.sleep(0.1 / speed)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()
    release_all()

def boss_died_reset():
    release_all()
    for _ in range(4):
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.1)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0)
    release_all()

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