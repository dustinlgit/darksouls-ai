import gymnasium as gym
from gymnasium import spaces

import numpy as np
import time
import math

from get_frame import get_one_frame
from memory import DS3Reader, BOSSES, ANIMATIONS, GUNDYR_ONE_HOT_ANIM
import controller

class DS3Env(gym.Env):
    MAX_DIST = 12

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
        self.action_space = spaces.MultiDiscrete([4, 4])
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(29,), dtype=np.float32)

        self.heal_count = 0

    def step(self, action):
        prev_player_norm_hp = self.player.norm_hp
        prev_boss_norm_hp = self.boss.norm_hp
        
        self.do_action(action)
        obs = self._get_observation(action)
        reward = self._calculate_reward(prev_player_norm_hp, prev_boss_norm_hp, action)
        terminated = self.player.hp <= 0 or self.boss.hp <= 0
        truncated = self.step_count >= self.max_steps

        self.step_count += 1
        
        info = {
            'player_hp': self.player.hp,
            'boss_hp': self.boss.hp,
            'is_success': bool(self.boss.hp <= 0 and self.player.hp > 0)
        }
        
        #self.ds3.ds3.write_int(self.boss._hp_addr, 0)
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
            self._wait_until_teleported()
            self._wait_until_loaded()
            controller.boss_died_reset()
            time.sleep(10)
        
        self._wait_until_loaded()
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


    def do_action(self, actions):
        move, act = actions

        match move:
            case 0:
                controller.move_forward()
            case 1:
                controller.move_back()
            case 2:
                controller.move_left()
            case 3:
                controller.move_right()

        match act:
            case 0:
                controller.attack()
            case 1:
                controller.dodge()
            case 2:
                controller.heal()
            case 3:
                controller.no_action()
        

    def _get_observation(self, action):
        """Get current observation (stats + frame)"""
        dist = math.dist(self.player.pos, self.boss.pos)
        norm_dist = min(dist, self.MAX_DIST) / self.MAX_DIST

        player_anim = self._encode_player_anim(self.player.animation)
        boss_anim = self._encode_boss_anim(self.boss.animation_str)
        stats = np.array([
            self.player.norm_hp, 
            self.player.norm_sp, 
            self.boss.norm_hp,
            norm_dist,
        ], dtype=np.float32)


        return np.concatenate([player_anim, boss_anim, stats])

    def _encode_player_anim(self, animation):
        encoding = np.zeros(shape=(4,), dtype=np.float32)
        if animation in ANIMATIONS.LIGHT_ATTACK:
            encoding[0] = 1
        elif animation in ANIMATIONS.HEAL:
            encoding[1] = 1
        elif animation in ANIMATIONS.DODGE:
            encoding[2] = 1
        else:
            encoding[3] = 1
        return encoding

    
    def _encode_boss_anim(self, animation_str):
        encoding = np.zeros(shape=(21,), dtype=np.float32);
        if animation_str in GUNDYR_ONE_HOT_ANIM:
            anim = GUNDYR_ONE_HOT_ANIM[animation_str]
        else:
            anim = 20
        encoding[anim] = 1
        return encoding

    

    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp, action):
        """Calculate reward based on state changes"""
        reward = 0.0
        
        # Reward for dealing damage to boss
        boss_damage = prev_boss_norm_hp - self.boss.norm_hp
        if boss_damage > 0:
            reward += boss_damage * 3 #increased
        
        # Penalty for taking damage
        player_damage = prev_player_norm_hp - self.player.norm_hp
        if player_damage > 0:
            reward -= player_damage * 2 #increased

        # Add penalty for being too far away; ~3 units is the
        #  attack range so little more leeway before penalty
        dist_to_boss = math.dist(self.player.pos, self.boss.pos)
        norm_dist = min(dist_to_boss, self.MAX_DIST) / self.MAX_DIST
        if norm_dist > 0.5:
            reward -= 0.05 * (norm_dist - 0.50) / 0.50 #larger penalty for being farther away vs close

        #add reward for being close to fight
        if norm_dist < 0.35:
            reward += 0.002
        
        # Large reward for killing boss
        if self.boss.hp <= 0:
            reward += 10
        
        # Large penalty for dying
        if self.player.hp <= 0:
            reward -= 2

        if self.player.sp <= 0:
            reward -= 0.01

        
        #pressure to quickly punish boss instead of rewarding random rolling and surviving actions
        reward -= 0.005
        
        return reward


    def _reset_mem(self):
        self.ds3.initialize()
        self.heal_count = 0
        self.player = self.ds3.player
        self.boss = self.ds3.boss


    def _wait_until_teleported(self):
        try:
            while self.player.y < 600:
                self.ds3.initialize()
        except Exception:
            ...
        time.sleep(5)


    def _wait_until_loaded(self):
        while True:
            try:
                self.ds3.initialize()
                if self.ds3.player.animation in ANIMATIONS.IDLE:
                    break
            except Exception:
                ...

        time.sleep(1.5)
