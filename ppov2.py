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
        8: ANIMATIONS.MOVE,
        9: ANIMATIONS.HEAL
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
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Dict({
            'stats': spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32),
            'frame': spaces.Box(low=0, high=255, shape=(128, 128, 1), dtype=np.uint8)
        })

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
            case 8:
                controller.heal()
        

    def _get_observation(self, action):
        """Get current observation (stats + frame)"""
        frame = get_one_frame()
        dist = math.dist(self.player.pos, self.boss.pos)
        norm_dist = min(dist, self.MAX_DIST) / self.MAX_DIST
        # Check if action was successful (action 0 is always "successful" as it's no action)
        if action == 0:
            action_success = True
        elif action in self.ACT_TO_ANI:
            action_success = self.player.animation in self.ACT_TO_ANI[action]
        else:
            action_success = False

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
    

    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp, action):
        """Calculate reward based on state changes - Optimized for boss killing"""
        reward = 0.0
        
        # Reward for dealing damage to boss (increased weight for consistency)
        boss_damage = prev_boss_norm_hp - self.boss.norm_hp
        if boss_damage > 0:
            # Scale reward by boss HP remaining (more valuable to finish off boss)
            boss_hp_remaining = self.boss.norm_hp
            damage_multiplier = 4.0 + (1.0 - boss_hp_remaining) * 2.0  # 4x to 6x scaling
            reward += boss_damage * damage_multiplier
        
        # Penalty for taking damage (increased to emphasize survival)
        player_damage = prev_player_norm_hp - self.player.norm_hp
        if player_damage > 0:
            # Scale penalty by player HP (worse to take damage when low)
            hp_frac = self.player.norm_hp
            damage_penalty = 3.0 + (1.0 - hp_frac) * 2.0  # 3x to 5x scaling
            reward -= player_damage * damage_penalty

        # Distance-based rewards (optimized for combat range)
        dist_to_boss = math.dist(self.player.pos, self.boss.pos)
        norm_dist = min(dist_to_boss, self.MAX_DIST) / self.MAX_DIST
        
        # Optimal combat range is 0.25-0.4 (close enough to attack, far enough to dodge)
        if 0.25 <= norm_dist <= 0.4:
            reward += 0.01  # Reward for being in optimal range
        elif norm_dist > 0.5:
            # Stronger penalty for being too far (can't attack effectively)
            reward -= 0.1 * (norm_dist - 0.5) / 0.5
        elif norm_dist < 0.2:
            # Small penalty for being too close (harder to dodge)
            reward -= 0.05 * (0.2 - norm_dist) / 0.2
        
        # Large reward for killing boss (increased for better signal)
        if self.boss.hp <= 0:
            reward += 20.0  # Increased from 10 to 20
        
        # Large penalty for dying (increased to emphasize survival)
        if self.player.hp <= 0:
            reward -= 10.0  # Increased from 2 to 10

        # Stamina management (small penalty for running out)
        if self.player.sp <= 0:
            reward -= 0.02

        # Small survival bonus (encourages staying alive longer)
        if self.player.hp > 0:
            reward += 0.001
        
        # Reward for successful actions (encourages action efficiency)
        if action in self.ACT_TO_ANI:
            action_success = self.player.animation in self.ACT_TO_ANI[action]
            if action_success:
                reward += 0.005
        
        # Healing logic (optimized)
        if(action == 8):
            # penalty for wasting flask when hp is high
            HEAL_AMT = 250 #how much hp you get for healing
            missing_hp = max(0.0, float(self.player.max_hp)) - float(self.player.hp)
            wasted_flask = max(0.0, HEAL_AMT - missing_hp)
            norm_wasted_flask = min(1.0, wasted_flask / HEAL_AMT)

            hp_frac = float(self.player.hp) / float(self.player.max_hp)
            #penalty for healing with high hp
            if hp_frac > 0.65 : #since health potion is roughly half of the players hp
                reward -= 0.5
            #reward healing at low health
            if hp_frac <= 0.45: #perfect percent for none wasted ...
                reward += 0.5 * (1.0 - norm_wasted_flask)
            
            # penalty if healed 3+ times in the episode
            self.heal_count+=1
            if self.heal_count > 3:
                reward -= 0.1 * (self.heal_count - 3) #lowered penalty
        
        # Small time penalty (encourages faster boss kills, but not too harsh)
        reward -= 0.001
        
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
