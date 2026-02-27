from collections import deque
import gymnasium as gym
from gymnasium import spaces

import numpy as np
import time
import math
from get_frame import open
from get_frame import get_one_frame
from memory import DS3Reader, BOSSES, ANIMATIONS
import controller
from pymem.exception import MemoryReadError
import pymem
ACTION_NAMES = {
    0: "NO_OP",
    1: "ATTACK",
    2: "DODGE",
    3: "ROLL",
    4: "FORWARD",
    5: "BACK",
    6: "RIGHT",
    7: "LEFT",
    8: "HEAL"
}
class DS3Env(gym.Env):
    MAX_DIST = 12

    # Animation codes for actions. Used to see if an action actually went through.
    ACT_TO_ANI = {
        1: ANIMATIONS.LIGHT_ATTACK,
        2: ANIMATIONS.DODGE, 
        3: ANIMATIONS.ROLL, 
        4: ANIMATIONS.MOVE, 
        5: ANIMATIONS.MOVE, 
        6: ANIMATIONS.MOVE, 
        7: ANIMATIONS.MOVE, 
        8: ANIMATIONS.HEAL 
    }


    def __init__(self):
        super().__init__()
        while True:
            try:
                self.ds3 = DS3Reader(BOSSES.IUDEX_GUNDYR)
                self.player = None
                self.boss = None
                self.ds3.attach()
                break
            except Exception as e:
                print("Memory reader could not be initialized. Dark Souls III Is probably not open. Error: ", e)
                print("Trying again: DS3Env")

        self.step_count = 0
        self.needs_refresh = True
        self.max_steps = 10000
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Dict({
            "stats": spaces.Box(low=-1.0, high=1.0, shape=(7,), dtype=np.float32),
        })
        
        self.ep_boss_dmg = 0
        self.ep_player_dmg = 0
        self.prev_player_hp = None
        self.prev_boss_hp = None

        self.heal_cd = 0
        self.step_dt = 0.35

    def step(self, action):
        try:
            t0 = time.time()

            self.ds3.ensure_attached()

            if self.needs_refresh or self.player is None or self.boss is None:
                self.ds3.refresh()
                self.player = self.ds3.player
                self.boss = self.ds3.boss
                self.needs_refresh = False

            prev_player_norm_hp = float(self.player.norm_hp)
            prev_boss_norm_hp   = float(self.boss.norm_hp)

            prev_norm_dist = float(min(self._safe_dist(), self.MAX_DIST) / self.MAX_DIST)

            prev_player_hp_abs = float(self.player.hp)
            prev_boss_hp_abs   = float(self.boss.hp)

            self.do_action(action)

            elapsed = time.time() - t0
            remaining = self.step_dt - elapsed
            if remaining > 0:
                time.sleep(remaining)
            boss_norm_min = float(self.boss.norm_hp)
            player_norm_min = float(self.player.norm_hp)
            for _ in range(6):          # ~0.12s
                time.sleep(0.02)
                boss_norm_min = min(boss_norm_min, float(self.boss.norm_hp))
                player_norm_min = min(player_norm_min, float(self.player.norm_hp))
            new_player_hp_abs = float(self.player.hp)
            new_boss_hp_abs   = float(self.boss.hp)

            p_dmg = max(0.0, prev_player_hp_abs - new_player_hp_abs)
            b_dmg = max(0.0, prev_boss_hp_abs - new_boss_hp_abs)

            if p_dmg < 1500:
                self.ep_player_dmg += p_dmg
            if b_dmg < 1500:
                self.ep_boss_dmg += b_dmg

            self.prev_player_hp = new_player_hp_abs
            self.prev_boss_hp = new_boss_hp_abs

            obs = self._get_observation(prev_player_norm_hp, prev_boss_norm_hp, prev_norm_dist)
            reward = self._calculate_reward(prev_player_norm_hp, prev_boss_norm_hp, player_norm_min, boss_norm_min, action)

            self.step_count += 1

            terminated = (self.player.hp <= 0) or (self.boss.hp <= 0)
            truncated = (self.step_count >= self.max_steps)

            if terminated or truncated:
                self.needs_refresh = True

            info = {
                "player_hp": self.player.hp,
                "boss_hp": self.boss.hp,
                "player_dmg": self.ep_player_dmg,
                "boss_dmg": self.ep_boss_dmg,
                "is_success": bool(self.boss.hp <= 0 and self.player.hp > 0),
            }
            return obs, reward, terminated, truncated, info

        except (MemoryReadError, pymem.exception.WinAPIError, RuntimeError) as e:
            self.needs_refresh = True
            self.player = None
            self.boss = None
            obs = self._get_observation(prev_player_norm_hp, prev_boss_norm_hp, prev_norm_dist)

            info = {
                "memory_error": True,
                "err": str(e),
                "player_hp": 0.0,
                "boss_hp": 0.0,
                "player_dmg": float(getattr(self, "ep_player_dmg", 0.0)),
                "boss_dmg": float(getattr(self, "ep_boss_dmg", 0.0)),
                "is_success": False,
            }
            return obs, -0.1, False, True, info
    

    def render(self):
        pass

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        try:
            self.ds3.ensure_attached()
            self.ds3.refresh()
            self.player = self.ds3.player
            self.boss = self.ds3.boss
            self.needs_refresh = False
        except (MemoryReadError, pymem.exception.WinAPIError, RuntimeError):
            # if refresh fails, re-init
            self.ds3.attach()
            self.ds3.refresh()
            self.player = self.ds3.player
            self.boss = self.ds3.boss
            self.needs_refresh = False
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

        self.heal_cd = 0
        
        self._wait_until_loaded()
        self._reset_mem()
        
        self.prev_player_hp = float(self.player.hp)
        self.prev_boss_hp = float(self.boss.hp)

        print("Walking to boss...")
        open.focus_window("DARK SOULS III")
        time.sleep(2)
        controller.walk_to_boss()
        
        self.step_count = 0
        self.boss_defeated = False
        self.step_dt = 0.35
        
        print(f"Reset complete")
        prev_player_norm_hp = self.player.norm_hp
        prev_boss_norm_hp = self.boss.norm_hp
        dist_to_boss = self._safe_dist()
        prev_norm_dist = min(dist_to_boss, self.MAX_DIST) / self.MAX_DIST
        obs = self._get_observation(prev_player_norm_hp, prev_boss_norm_hp, prev_norm_dist)
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
        
    def _get_observation(self, prev_player_norm_hp, prev_boss_norm_hp, prev_norm_dist):
        """Get current observation (stats + frame)"""
        dist = self._safe_dist()
        norm_dist = min(dist, self.MAX_DIST) / self.MAX_DIST
        norm_dist = float(np.clip(norm_dist, 0.0, 1.0))

        player_norm_hp = float(self._safe_read(lambda: self.player.norm_hp, 0.0))
        player_norm_sp = float(self._safe_read(lambda: self.player.norm_sp, 0.0))
        boss_norm_hp   = float(self._safe_read(lambda: self.boss.norm_hp, 0.0))

        d_player_hp = float(np.clip(player_norm_hp - prev_player_norm_hp, -1.0, 1.0))
        d_boss_hp   = float(np.clip(prev_boss_norm_hp - boss_norm_hp, -1.0, 1.0))  # >0 means boss took damage
        d_dist      = float(np.clip(norm_dist - prev_norm_dist, -1.0, 1.0))

        stats = np.array(
            [
                player_norm_hp,
                player_norm_sp,
                boss_norm_hp,
                norm_dist,
                d_player_hp,
                d_boss_hp,
                d_dist,
            ],
            dtype=np.float32
        )

        return {"stats": stats}
    
    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp, player_norm_min, boss_norm_min, action):
        reward = 0.0
        dealt = max(0.0, float(prev_boss_norm_hp) - float(boss_norm_min))
        taken = max(0.0, float(prev_player_norm_hp) - float(player_norm_min))

        # ++ aggressive 
        reward = 12.0 * dealt - 6.0 * taken

        # -- anti-stall
        reward -= 0.002

        if self.boss.hp <= 0:   reward += 15.0
        if self.player.hp <= 0: reward -= 15.0

        return float(reward)

        return reward

    def _reset_mem(self):
        self.ds3.initialize()
        self.player = self.ds3.player
        self.boss = self.ds3.boss
        self.needs_refresh = False


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
