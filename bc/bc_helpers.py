import json
from pynput import keyboard, mouse
import time
import os
import threading

key_state = {
    "forward": False,#w
    "backward": False, #s
    "left": False, #a
    "right": False, #d
    "dodge": False, #(space) or (w + space) (merge both dodges)
    "attack": False, #right click
    "lock_on": False, #q
    "heal": False #r
}
log = []
FPS = 15
episode_id = 0
attack_pulse = False
def attacked(x, y, button, pressed):
    # right mouse button = attack
    global attack_pulse, click_count
    if button == mouse.Button.left and pressed:
        attack_pulse = True

def keyDown(key):
    try:
        if key.char == 'w': key_state["forward"] = True
        elif key.char == 's': key_state["backward"] = True
        elif key.char == 'a': key_state["left"] = True
        elif key.char == 'd': key_state["right"] = True
        elif key.char == 'q': key_state["lock_on"] = True
        elif key.char == 'r': key_state["heal"] = True
    except AttributeError:
        if key == keyboard.Key.space:
            key_state["dodge"] = True

def keyUp(key):
    try:
        if key.char == 'w': key_state["forward"] = False
        elif key.char == 's': key_state["backward"] = False
        elif key.char == 'a': key_state["left"] = False
        elif key.char == 'd': key_state["right"] = False
        elif key.char == 'q': key_state["lock_on"] = False
        elif key.char == 'r': key_state["heal"] = False
    except AttributeError:
        if key == keyboard.Key.space:
            key_state["dodge"] = False

ACTION_ORDER = ["attack","dodge","forward","backward","left","right","lock_on","heal"]
def encode_action(ks):
     return [int(ks[k]) for k in ACTION_ORDER]

mouse_listener = mouse.Listener(on_click=attacked)
mouse_listener.start()
keyboard.Listener(on_press=keyDown, on_release=keyUp).start()

timestamp = time.strftime("%Y%m%d_%H%M%S")
SAVE_DIR = "bc_logs"
os.makedirs(SAVE_DIR, exist_ok=True)

filename = f"ds3_bc_ep{episode_id}_{timestamp}.jsonl"
save_path = os.path.join(SAVE_DIR, filename)

def logger():
    global attack_pulse
    frame_idx = 0
    while True:
        try:
            key_state["attack"] = attack_pulse
            attack_pulse = False
            action_vec = encode_action(key_state)
            log.append({"episode": episode_id, "frame": frame_idx, "action": action_vec})
            frame_idx += 1
            time.sleep(1/FPS)
        except:
            with open(save_path, "w") as f:
                for entry in log:
                    f.write(json.dumps(entry) + "\n")
                print(f"Saved {len(log)} frames to {save_path}")
            break
logger()