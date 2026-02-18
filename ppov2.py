import gymnasium as gym
from gymnasium import spaces

import numpy as np
import time
import math

from get_frame import get_one_frame
from memory import DS3Reader, BOSSES, ANIMATIONS
import controller
from pymem.exception import MemoryReadError


class DS3Env(gym.Env):
    MAX_DIST = 12

    # Animation codes for actions. Used to see if an action actually went through.
    ACT_TO_ANI = {
        1: ANIMATIONS.LIGHT_ATTACK, #0
        2: ANIMATIONS.LIGHT_ATTACK, #1
        3: ANIMATIONS.DODGE, #2
        4: ANIMATIONS.ROLL, #3
        5: ANIMATIONS.MOVE, #4
        6: ANIMATIONS.MOVE, #5
        7: ANIMATIONS.MOVE, #6
        8: ANIMATIONS.MOVE, #7
        9: ANIMATIONS.HEAL #8
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
        
        self.ep_boss_dmg = 0
        self.ep_player_dmg = 0
        self.heal_count = 0
    
    def step(self, action):
        try:
            self.ds3.initialize()
            self.player = self.ds3.player
            self.boss = self.ds3.boss
        except Exception:
            obs = self._get_observation(action=0)
            return obs, -0.1, False, True, {"memory_error": True}

        prev_player_norm_hp = self.player.norm_hp
        prev_boss_norm_hp = self.boss.norm_hp

        self.do_action(action)
        obs = self._get_observation(action)
        reward = self._calculate_reward(prev_player_norm_hp, prev_boss_norm_hp, action)

        self.step_count += 1

        terminated = (self.player.hp <= 0) or (self.boss.hp <= 0)
        truncated = (self.step_count >= self.max_steps)

        boss_damage = max(0.0, prev_boss_norm_hp - self.boss.norm_hp)
        player_damage = max(0.0, prev_player_norm_hp - self.player.norm_hp)

        self.ep_boss_dmg += boss_damage
        self.ep_player_dmg += player_damage

        info = {
            "player_hp": self.player.hp,
            "boss_hp": self.boss.hp,
            "is_success": bool(self.boss.hp <= 0 and self.player.hp > 0),
        }

        if terminated or truncated:
            print("EP boss_dmg:", self.ep_boss_dmg,
                "player_dmg:", self.ep_player_dmg,
                "success:", info["is_success"])

            info["episode"] = {
                "boss_dmg": float(self.ep_boss_dmg),
                "player_dmg": float(self.ep_player_dmg),
                "len": int(self.step_count),
                "success": float(info["is_success"]),
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
            self._wait_until_teleported()
            self._wait_until_loaded()
            controller.boss_died_reset()
            time.sleep(10)
        self.ep_boss_dmg = 0.0
        self.ep_player_dmg = 0.0
        self.heal_count = 0
        
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

    def _safe_dist(self):
        try:
            d = float(math.dist(self.player.pos, self.boss.pos))
        except Exception:
            return self.MAX_DIST
        if not np.isfinite(d):
            return self.MAX_DIST
        return d
    
    def _safe_read(self, func, default=0):
        try:
            return func()
        except:
            print("Read was not safe from function: ", func.__name__)
            return default

    def _safe_animation(self, default=None):
        try:
            return self.player.animation
        except MemoryReadError:
            return default
        except Exception:
            return default
        
    def _get_observation(self, action):
        """Get current observation (stats + frame)"""
        frame = get_one_frame()
        dist = self._safe_dist()
        norm_dist = min(dist, self.MAX_DIST) / self.MAX_DIST
        ani = self._safe_animation(default=None)
        #action_success = action == 0 or self.player.animation in self.ACT_TO_ANI[action]
        ani = self._safe_animation(default=None)
        if action == 0:
            action_success = 1.0
        else:
            expected = self.ACT_TO_ANI.get(action, [])
            action_success = 1.0 if (ani is not None and ani in expected) else 0.0
        stats = np.array(
            [
                self._safe_read(lambda: self.player.norm_hp, 0.0),
                self._safe_read(lambda: self.player.norm_sp, 0.0),
                self._safe_read(lambda: self.boss.norm_hp, 0.0),
                norm_dist,
                action_success
            ], 
            dtype=np.float32
        )


        return {'stats': stats, 'frame': frame}
    
    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp, action):
        """Calculate reward based on state changes"""
        ATTACK_ACT = (0,1)
        DEFENSE_ACT = (3,4)
        
        reward = 0.0
        # Reward for dealing damage to boss
        boss_damage = prev_boss_norm_hp - self.boss.norm_hp
        dist_to_boss = self._safe_dist()
        norm_dist = min(dist_to_boss, self.MAX_DIST) / self.MAX_DIST

        if boss_damage > 0:
            reward += boss_damage * 4 
            #reward good attacking (damages boss with action)
            if action in ATTACK_ACT:
                reward += 0.05
        else:
            # penalty for stalling...
            if norm_dist < 0.38:
                reward -= 0.01

        if action in ATTACK_ACT and norm_dist <= 0.30:
            reward += 0.02 * (1.0 - norm_dist / 0.30)

        # Penalty for taking damage
        player_damage = prev_player_norm_hp - self.player.norm_hp
        if player_damage > 0:
            reward -= player_damage * 2 #increased
        else: #no dmg taken, and it rolled/dodge when it was close to the boss (actually matters)
            if action in DEFENSE_ACT and norm_dist < 0.4:
                reward += 0.003
        #rolling sitll penalized so it learns its not all good to just roll around
        if action in DEFENSE_ACT:
            reward -= 0.02
        # Add penalty for being too far away; ~3 units is the
        #  attack range so little more leeway before penalty
        reward += 0.02 * (1.0 - norm_dist)
        if norm_dist > 0.55:
            reward -= 0.03 * (norm_dist - 0.55) / 0.45

        # Large reward for killing boss
        if self.boss.hp <= 0:
            reward += 10
        
        # Large penalty for dying
        if self.player.hp <= 0:
            reward -= 6 #increased by 1x

        # better stamina rewards that slowly discourages high sp use
        sp_frac = 0.0
        if float(self.player.max_sp) > 0:
            sp_frac = float(self.player.sp) / max(1.0, float(self.player.max_sp))
        if sp_frac < 0.10:
            reward -= 0.02
        if self.player.sp <= 0:
            reward -= 0.03

        #pressure to quickly punish boss instead of rewarding random rolling and surviving actions
        reward -= 0.005
        
        if(action == 8):
            # penalty for wasting flask when hp is high
            HEAL_AMT = 250 #how much hp you get for healing
            missing_hp = max(0.0, (float(self.player.max_hp) - float(self.player.hp)))
            wasted_flask = max(0.0, HEAL_AMT - missing_hp)
            norm_wasted_flask = min(1.0, wasted_flask / HEAL_AMT)
            if(float(self.player.max_hp) > 0): #only when hp is valid we calculate rewards using hp 
                hp_frac = float(self.player.hp) / max(1, float(self.player.max_hp))
                #penalty for healing with high hp
                if hp_frac > 0.65 : #since health potion is roughly half of the players hp
                    reward -= 0.2
                #reward healing at low health
                if hp_frac <= 0.45: #perfect percent for none wasted ...
                    reward += 0.5 * (1.0 - norm_wasted_flask)
            
            # penalty if healed 3+ times in the episode
            self.heal_count+=1
            if self.heal_count > 3:
                reward -= 0.05 * (self.heal_count - 3) #lowered penalty
        return reward


    def _reset_mem(self):
        self.ds3.initialize()
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
