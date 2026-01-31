import actions
import time
import gymnasium as gym
from gymnasium import spaces

class ds3Env(gym.Env):
    def __init__(self):
        self.player_hp = None
        self.player_max_hp
        self.player_sp = None
        self.player_max_sp = None

        self.boss_hp = None
        self.boss_max_hp = None

    def do_action(self, a, duration = 0.1): #can change duration later
        '''core function for learning optimal actions'''
        if a == 0:
            time.sleep(duration) #no action
        elif a == 1:
            actions.right_hand_light_attack()
        elif a == 2:
            actions.forward_run_attack()
        elif a == 3:
            actions.dodge()
        elif a == 4:
            actions.forward_roll_dodge()
        elif a == 5:    
            actions.shield(duration)
        elif a == 6:
            actions.run_forward(duration)
        elif a == 7:
            actions.run_back(duration)
        elif a == 8:
            actions.run_right(duration)
        elif a == 9:
            actions.run_left(duration)
        elif a == 10:
            actions.heal()

    def step(self, action):
        '''keep track of the step count, 
        execute chosen action, 
        observe new state (get stats),
        compute reward,
        update memory variables,
        see if player is dead OR boss is dead'''
        return
    
    def reset(self):
        '''must reset the boss fight, unpress all keys, reset variables used to train again'''
        return
    
