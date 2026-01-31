import subprocess
from pathlib import Path
import pydirectinput as pdi
import time

def right_hand_light_attack():
    pdi.click()

def forward_run_attack():
    pdi.keyDown("w")
    pdi.keyUp("w")
    pdi.click()

def dodge():
    pdi.keyDown(" ")
    pdi.keyUp(" ")

def forward_roll_dodge():
    pdi.keyDown("w")
    pdi.keyDown(" ")
    pdi.keyUp(" ")
    pdi.keyUp("w")

def shield(sec):
    pdi.mouseDown(button='right')
    time.sleep(sec)
    pdi.mouseUp(button='right')

def run_forward(sec):
    pdi.keyDown("w")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("w")
    pdi.keyUp(" ")

def run_back(sec):
    pdi.keyDown("s")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("s")
    pdi.keyUp(" ")


def run_right(sec):
    pdi.keyDown("d")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("d")
    pdi.keyUp(" ")


def run_left(sec):
    pdi.keyDown("a")
    pdi.keyDown(" ")
    time.sleep(sec) 
    pdi.keyUp("a")
    pdi.keyUp(" ")

def heal():
    pdi.press("r")

#this prob irrelevant to project, but might help if we use pydirectinput

(leah, jason, dustin) = (True, False, False) #CHANGE! 

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