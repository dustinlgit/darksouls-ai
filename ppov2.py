import actions
import time
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from memory import DS3Reader, BOSSES
from get_frame import get_one_frame

class DS3Env(gym.Env):
    RUNNING = 0
    PLAYER_WIN = 1
    PLAYER_DEATH = 2


    def __init__(self):
        super().__init__()
        
        try:
            self.state = DS3Reader(BOSSES.IUDEX_GUNDYR)
        except Exception as e:
            raise RuntimeError("Memory reader could not be initialized. Dark Souls III Is probably not open. Error: ", e)

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
        

    def _get_observation(self):
        """Get current observation (stats + frame)"""
        distance = 0.5  # Placeholder - could calculate from frame or memory
        
        stats = np.array([self.player.norm_hp, self.player.norm_sp, self.boss.norm_hp, distance], dtype=np.float32)
        
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
    

    def _calculate_reward(self, prev_player_hp, prev_boss_hp):
        """Calculate reward based on state changes"""
        reward = 0.0
        
        # Reward for dealing damage to boss
        if prev_boss_hp > 0:
            boss_damage = prev_boss_hp - self.boss.hp
            if boss_damage > 0:
                reward += boss_damage * 0.1  # Reward for dealing damage
        
        # Penalty for taking damage
        if prev_player_hp > 0:
            player_damage = prev_player_hp - self.player.hp
            if player_damage > 0:
                reward -= player_damage * 0.2  # Penalty for taking damage
        
        # Large reward for killing boss
        if self.boss.hp <= 0:
            reward += 1000.0
        
        # Large penalty for dying
        if self.player.hp <= 0:
            reward -= 500.0
        
        # Small survival reward
        reward += 0.1
        
        # Penalty for running out of stamina (encourages stamina management)
        if self.player.sp < 10:
            reward -= 0.05
        
        return reward

    def do_action(self, a, duration=0.5):
        '''core function for learning optimal actions'''
        if a == 0:
            time.sleep(0.05) #no action
        elif a == 1:
            actions.right_hand_light_attack()
            time.sleep(0.5)
        elif a == 2:
            actions.forward_run_attack()
            time.sleep(0.5)
        elif a == 3:
            actions.dodge()
            time.sleep(0.5)
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
        prev_player_hp = self.player.hp
        prev_boss_hp = self.boss.hp

        print("Performed action: ", action)
        # Execute action
        self.do_action(action)
        
        # Get observation
        obs = self._get_observation()
        
        # Calculate reward
        reward = self._calculate_reward(prev_player_hp, prev_boss_hp)
        
        # Check if episode is done
        if self.player.hp <= 0:
            terminated = self.PLAYER_DEATH
        elif self.boss.hp <= 0:
            terminated = self.PLAYER_WIN
        else:
            terminated = self.RUNNING

        truncated = self.step_count >= self.max_steps
        
        self.step_count += 1
        
        info = {
            'player_hp': self.player.hp,
            'boss_hp': self.boss.hp,
        }
        
        return obs, reward, terminated, truncated, info


    def reset(self, last_episode_win=False, seed=None):
        '''must reset the boss fight, unpress all keys, reset variables used to train again'''
        super().reset(seed=seed)
        
        # Release all keys first to ensure clean state
        actions.release_all_keys()
        time.sleep(1)
        
        if last_episode_win:
            # Boss dead, reset boss arena
            print("Boss dead, resetting arena (15 seconds)...")
            time.sleep(15)
            actions.boss_died_reset()
            time.sleep(10)
        
        else:
            # Player dead, wait for respawn and reinitialize pointers
            print("Waiting for respawn (10 seconds)...")
            time.sleep(10)
        
        # Walk to boss
        print("Walking to boss...")
        actions.walk_to_boss()
        
        # Reset state variables
        self.step_count = 0
        
        print(f"Reset complete")


    def reset_state(self):
        self.state.initialize()
        self.player = self.state.player
        self.boss = self.state.boss