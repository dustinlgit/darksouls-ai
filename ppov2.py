import gymnasium as gym
from gymnasium import spaces

import numpy as np
import time
import math

from get_frame import get_one_frame
from memory import DS3Reader, BOSSES, ANIMATIONS
import controller

class DS3Env(gym.Env):
    MAX_DIST = 12

    # Animation codes for actions. Used to see if an action actually went through.
    ACT_TO_ANI = {
        1: ANIMATIONS.LIGHT_ATTACK,
        2: ANIMATIONS.LIGHT_ATTACK,
        3: ANIMATIONS.DODGE,
        4: ANIMATIONS.ROLL,
        5: ANIMATIONS.MOVE,
        6: ANIMATIONS.MOVE,
        7: ANIMATIONS.MOVE,
        8: ANIMATIONS.MOVE
    }


    def __init__(self):
        super().__init__()
        
        try:
            self.ds3 = DS3Reader(BOSSES.IUDEX_GUNDYR)
            self.player = None
            self.boss = None
        except Exception as e:
            raise RuntimeError("Memory reader could not be initialized. Dark Souls III Is probably not open. Error: ", e)

        self.step_count = 0
        self.max_steps = 10000
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Dict({
            'stats': spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32),
            'frame': spaces.Box(low=0, high=255, shape=(128, 128, 1), dtype=np.uint8)
        })


    def step(self, action):
        prev_player_norm_hp = self.player.norm_hp
        prev_boss_norm_hp = self.boss.norm_hp
        

        print("Performed action: ", action)

        self.do_action(action)
        obs = self._get_observation(action)
        reward = self._calculate_reward(prev_player_norm_hp, prev_boss_norm_hp)
        terminated = self.player.hp <= 0 or self.boss.hp <= 0
        truncated = self.step_count >= self.max_steps

        self.step_count += 1
        
        info = {
            'player_hp': self.player.hp,
            'boss_hp': self.boss.hp,
        }

        return obs, reward, terminated, truncated, info
    

    def render(self):
        pass


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        controller.keep_ds3_alive()
        
        # Release all keys first to ensure clean state
        controller.release_all_keys()
        time.sleep(1)
        
        if self.boss and self.boss.hp <= 0:
            print("Boss dead, resetting arena (15 seconds)...")
            time.sleep(15)
            controller.boss_died_reset()
            time.sleep(10)
        
        else:
            print("Waiting for respawn (18 seconds)...")
            time.sleep(18)

        self._reset_mem()
        
        print("Walking to boss...")
        controller.walk_to_boss()
        
        self.step_count = 0
        self.boss_defeated = False
        
        print(f"Reset complete")

        obs = self._get_observation(action=0)
        info = {
            "player_hp": self.player.hp,
            "boss_hp": self.boss.hp
        }

        return obs, info


    def do_action(self, a, duration=0.1):
        '''core function for learning optimal actions'''

        match a:
            case 0:
                # No acation
                time.sleep(duration)
            case 1:
                controller.right_hand_light_attack()
            case 2:
                controller.dodge()
            case 3:
                controller.forward_roll_dodge()
            case 4:
                controller.run_forward(duration)
            case 5:
                controller.run_back(duration)
            case 6:
                controller.run_right(duration)
            case 7:
                controller.run_left(duration)
        

    def _get_observation(self, action):
        """Get current observation (stats + frame)"""
        frame = get_one_frame()
        dist = math.dist(self.player.pos, self.boss.pos)
        norm_dist = min(dist, self.MAX_DIST) / self.MAX_DIST
        action_success = action == 0 or self.player.animation in self.ACT_TO_ANI[action]

        stats = np.array(
            [
                self.player.norm_hp, 
                self.player.norm_sp, 
                self.boss.norm_hp,
                norm_dist,
                action_success
            ], 
            dtype=np.float32
        )


        return {'stats': stats, 'frame': frame}
    

    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp):
        """Calculate reward based on state changes"""
        reward = 0.0
        
        # Reward for dealing damage to boss
        boss_damage = prev_boss_norm_hp - self.boss.norm_hp
        if boss_damage > 0:
            reward += boss_damage * 2 
        
        # Penalty for taking damage
        player_damage = prev_player_norm_hp - self.player.norm_hp
        if player_damage > 0:
            reward -= player_damage * 0.5 

        # Add penalty for being too far away; ~3 units is the
        #  attack range so little more leeway before penalty
        dist_to_boss = math.dist(self.player.pos, self.boss.pos)
        norm_dist = min(dist_to_boss, self.MAX_DIST) / self.MAX_DIST
        if norm_dist > 0.5:
            reward -= norm_dist * 0.01
        
        # Large reward for killing boss
        if self.boss.hp <= 0:
            reward += 10
        
        # Large penalty for dying
        if self.player.hp <= 0:
            reward -= 2

        if self.player.sp <= 0:
            reward -= 0.01
        
        return reward


    def _reset_mem(self):
        self.ds3.initialize()
        self.player = self.ds3.player
        self.boss = self.ds3.boss
