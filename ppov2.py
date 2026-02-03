import actions
import time
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pymem
from memory import utils
from get_frame import get_one_frame
import cv2

class ds3Env(gym.Env):
    def __init__(self):
        super().__init__()
        
        # Initialize memory reading
        try:
            self.ds3 = pymem.Pymem("DarkSoulsIII.exe")
            self.module = pymem.process.module_from_name(self.ds3.process_handle, "DarkSoulsIII.exe")
            self.world_chr_man = utils.get_world_chr_man(self.ds3, self.module)
            self.player_stats = utils.follow_chain(self.ds3, self.world_chr_man, [0x80, 0x1F90, 0x18])
            self.iudex_gundyr = utils.get_entity(self.ds3, self.world_chr_man, utils.IUDEX_GUNDYR)
        except Exception as e:
            print(f"Warning: Could not initialize memory reading: {e}")
            self.ds3 = None
        
        # Memory offsets
        self.player_curr_hp_offset = 0xD8
        self.player_max_hp_offset = 0xDC
        self.player_curr_sp_offset = 0xF0
        self.player_max_sp_offset = 0xF4
        self.boss_curr_hp_offset = 0xD8
        self.boss_max_hp_offset = 0xDC
        
        # State variables
        self.player_hp = None
        self.player_max_hp = None
        self.player_sp = None
        self.player_max_sp = None
        self.boss_hp = None
        self.boss_max_hp = None
        self.prev_player_hp = None
        self.prev_boss_hp = None
        self.step_count = 0
        self.max_steps = 10000
        
        # Action space: 11 discrete actions
        self.action_space = spaces.Discrete(11)
        
        # Observation space: normalized stats + frame
        # Stats: player_hp_ratio, player_sp_ratio, boss_hp_ratio, distance (placeholder)
        # Frame: 400x400x3 RGB image (will be resized/flattened or use CNN)
        self.observation_space = spaces.Dict({
            'stats': spaces.Box(low=0, high=1, shape=(4,), dtype=np.float32),
            'frame': spaces.Box(low=0, high=255, shape=(400, 400, 3), dtype=np.uint8)
        })
        
    def _get_game_state(self):
        """Read current game state from memory"""
        if self.ds3 is None:
            # Return default values if memory reading fails
            return {
                'player_hp': 1000,
                'player_max_hp': 1000,
                'player_sp': 100,
                'player_max_sp': 100,
                'boss_hp': 1000,
                'boss_max_hp': 1000
            }
        
        try:
            player_curr_hp = self.player_stats + self.player_curr_hp_offset
            player_max_hp = self.player_stats + self.player_max_hp_offset
            player_curr_sp = self.player_stats + self.player_curr_sp_offset
            player_max_sp = self.player_stats + self.player_max_sp_offset
            boss_curr_hp = self.iudex_gundyr + self.boss_curr_hp_offset
            boss_max_hp = self.iudex_gundyr + self.boss_max_hp_offset

            self.player_hp = self.ds3.read_int(player_curr_hp)
            self.player_max_hp = self.ds3.read_int(player_max_hp)
            self.player_sp = self.ds3.read_int(player_curr_sp)
            self.player_max_sp = self.ds3.read_int(player_max_sp)
            self.boss_hp = self.ds3.read_int(boss_curr_hp)
            self.boss_max_hp = self.ds3.read_int(boss_max_hp)
            return {
                'player_hp': self.player_hp,
                'player_max_hp': self.player_max_hp,
                'player_sp': self.player_sp,
                'player_max_sp': self.player_max_sp,
                'boss_hp': self.boss_hp,
                'boss_max_hp': self.boss_max_hp
            }
        except Exception as e:
            print(f"Error reading game state: {e}")
            return {
                'player_hp': self.player_hp or 1000,
                'player_max_hp': self.player_max_hp or 1000,
                'player_sp': self.player_sp or 100,
                'player_max_sp': self.player_max_sp or 100,
                'boss_hp': self.boss_hp or 1000,
                'boss_max_hp': self.boss_max_hp or 1000
            }
    
    def _get_observation(self):
        """Get current observation (stats + frame)"""
        state = self._get_game_state()
        
        # Normalize stats
        player_hp_ratio = state['player_hp'] / state['player_max_hp']
        player_sp_ratio = state['player_sp'] / state['player_max_sp']
        boss_hp_ratio = state['boss_hp'] / state['boss_max_hp']
        self.player_hp = state['player_hp']
        distance = 0.5  # Placeholder - could calculate from frame or memory
        
        stats = np.array([player_hp_ratio, player_sp_ratio, boss_hp_ratio, distance], dtype=np.float32)
        
        # Get frame
        try:
            frame = get_one_frame()
            if frame is None:
                # Return black frame if capture fails
                frame = np.zeros((400, 400, 3), dtype=np.uint8)
        except Exception as e:
            print(f"Error getting frame: {e}")
            frame = np.zeros((400, 400, 3), dtype=np.uint8)
        
        return {'stats': stats, 'frame': frame}
    
    def _calculate_reward(self, state, prev_state):
        """Calculate reward based on state changes"""
        reward = 0.0
        
        # Reward for dealing damage to boss
        if prev_state and prev_state['boss_hp'] > 0:
            boss_damage = prev_state['boss_hp'] - state['boss_hp']
            if boss_damage > 0:
                reward += boss_damage * 0.1  # Reward for dealing damage
        
        # Penalty for taking damage
        if prev_state and prev_state['player_hp'] > 0:
            player_damage = prev_state['player_hp'] - state['player_hp']
            if player_damage > 0:
                reward -= player_damage * 0.2  # Penalty for taking damage
        
        # Large reward for killing boss
        if state['boss_hp'] <= 0:
            reward += 1000.0
        
        # Large penalty for dying
        if state['player_hp'] <= 0:
            reward -= 500.0
        
        # Small survival reward
        reward += 0.1
        
        # Penalty for running out of stamina (encourages stamina management)
        if state['player_sp'] < 10:
            reward -= 0.05
        
        return reward

    def do_action(self, a, duration=1.5):
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
        
        # Store previous state
        prev_state = {
            'player_hp': self.player_hp,
            'boss_hp': self.boss_hp
        }

        print("Performed action: ", action)
        # Execute action
        self.do_action(action)
        
        # Small delay to let game state update
        time.sleep(0.05)
        
        # Get new state
        state = self._get_game_state()
        self.player_hp = state['player_hp']
        self.player_max_hp = state['player_max_hp']
        self.player_sp = state['player_sp']
        self.player_max_sp = state['player_max_sp']
        self.boss_hp = state['boss_hp']
        self.boss_max_hp = state['boss_max_hp']
        
        # Get observation
        obs = self._get_observation()
        
        # Calculate reward
        reward = self._calculate_reward(state, prev_state)
        
        # Check if episode is done
        terminated = state['player_hp'] <= 0 or state['boss_hp'] <= 0
        truncated = self.step_count >= self.max_steps
        
        self.step_count += 1
        
        info = {
            'player_hp': self.player_hp,
            'boss_hp': self.boss_hp,
            'step': self.step_count
        }
        
        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        '''must reset the boss fight, unpress all keys, reset variables used to train again'''
        super().reset(seed=seed)
        state = self._get_game_state()
        # handle boss dead / player dead
        player_dead = state['player_hp'] <= 0
        boss_dead = state['boss_hp'] <= 0
        if(not boss_dead and not player_dead):
            actions.walk_to_boss()
        elif(player_dead):
            time.sleep(15)
            actions.walk_to_boss()
        elif(boss_dead):
            time.sleep(15)
            actions.boss_died_reset()
            time.sleep(10)
            actions.walk_to_boss()
        print("Player dead: ", player_dead)
        print("Boss dead: ", boss_dead)
        actions.walk_to_boss()
        # Reset state variables
        self.step_count = 0
        self.prev_player_hp = None
        self.prev_boss_hp = None

        # Get initial state
        state = self._get_game_state()
        self.player_hp = state['player_hp']
        self.player_max_hp = state['player_max_hp']
        self.player_sp = state['player_sp']
        self.player_max_sp = state['player_max_sp']
        self.boss_hp = state['boss_hp']
        self.boss_max_hp = state['boss_max_hp']
        
        # Get initial observation
        obs = self._get_observation()
        
        info = {
            'player_hp': self.player_hp,
            'boss_hp': self.boss_hp
        }
        
        return obs, info
