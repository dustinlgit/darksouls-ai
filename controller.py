import vgamepad as vg
import time
import win32gui
import win32con

# Set to 2.0 when the game is running at 2x speed so all durations scale down
SPEED = 1.0

def heal():
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    gamepad.update()
    time.sleep(0.08 / SPEED)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
    gamepad.update()

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

def set_movement(x_val, y_val):
    """Set left joystick position for directional movement."""
    gamepad.left_joystick_float(x_value_float=x_val, y_value_float=y_val)
    gamepad.update()

def right_hand_light_attack():
    # RB on Xbox
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()
    time.sleep(0.1 / SPEED)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()

def forward_run_attack():
    # Tilt stick forward + RB
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)
    gamepad.update()
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    gamepad.update()
    time.sleep(0.1 / SPEED)
    gamepad.reset()
    gamepad.update()

def dodge():
    # Tap B
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(0.05 / SPEED)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()

def forward_roll_dodge():
    # Forward + B
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(0.05 / SPEED)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()

def run_forward(sec):
    # Forward + Hold B
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=1.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec / SPEED)
    gamepad.reset()
    gamepad.update()

def run_back(sec):
    # Back + Hold B
    gamepad.left_joystick_float(x_value_float=0.0, y_value_float=-1.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec / SPEED)
    gamepad.reset()
    gamepad.update()

def run_right(sec):
    # Right + Hold B
    gamepad.left_joystick_float(x_value_float=1.0, y_value_float=0.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec / SPEED)
    gamepad.reset()
    gamepad.update()

def run_left(sec):
    # Left + Hold B
    gamepad.left_joystick_float(x_value_float=-1.0, y_value_float=0.0)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
    gamepad.update()
    time.sleep(sec / SPEED)
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
        time.sleep(0.1 / SPEED)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0 / SPEED)

    run_forward(5.0)
    # Lock on (RS Click)
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()
    time.sleep(0.1 / SPEED)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()

def boss_died_reset():
    release_all_keys()
    for _ in range(4):
        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(0.1 / SPEED)
        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        gamepad.update()
        time.sleep(1.0 / SPEED)

def lock_on():
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()

    time.sleep(1.0 / SPEED) 

    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    gamepad.update()


def turn_lock_on(min_deg=90, max_deg=180):
    gamepad.right_joystick(x_value=32767, y_value=0)
    gamepad.update()
    time.sleep(1.0 / SPEED)
    gamepad.right_joystick(x_value=0, y_value=0)
    gamepad.update()

    lock_on()