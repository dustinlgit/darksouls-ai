from collections import deque
import gymnasium as gym
from gymnasium import spaces

import numpy as np
import time
import math
from get_frame import open
from get_frame import get_one_frame
from memory import DS3Reader, BOSSES, ANIMATIONS, GUNDYR_ONE_HOT_ANIM
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
    SPEED = 1
    MAX_DIST = 12
    FRAME_SKIP = 15
    FRAME_DELAY = FRAME_SKIP / 60 / SPEED
    MAX_DIST = 12

    # Left joystick (x, y) for each movement index
    _MOVE_JOYSTICK = {
        0: (0.0,  1.0),  #forward
        1: (0.0, -1.0),  #back
        2: (-1.0,  0.0),  #left
        3: (1.0,  0.0),  #right
        4: (0.0,  0.0),  #neutral
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

        controller.SPEED = self.SPEED
        self.step_count = 0
        self.needs_refresh = True
        self.max_steps = 10000
        # [movement: 0=fwd,1=back,2=left,3=right,4=neutral] x [action: 0=attack,1=dodge,2=heal,3=none]
        self.action_space = spaces.MultiDiscrete([5, 4])
        # 5 (player_anim) + 21 (boss_anim) + 5 (stats: hp, sp, boss_hp, dist, boss_anim_prog) = 31
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(31,), dtype=np.float32)
        
        self.ep_boss_dmg = 0
        self.ep_player_dmg = 0
        self.prev_player_hp = None
        self.prev_boss_hp = None

        self.heal_cd = 0

    def step(self, action):
        try:
            self.ds3.ensure_attached()

            if self.needs_refresh or self.player is None or self.boss is None:
                self.ds3.refresh()
                self.player = self.ds3.player
                self.boss = self.ds3.boss
                self.needs_refresh = False
            if not self.ds3.locked_on:
                controller.lock_on()
                if not self.ds3.locked_on:
                    controller.turn_lock_on()
            prev_player_norm_hp = float(self.player.norm_hp)
            prev_boss_norm_hp   = float(self.boss.norm_hp)

            prev_player_hp_abs = float(self.player.hp)
            prev_boss_hp_abs   = float(self.boss.hp)

            self.do_action(action)
            time.sleep(self.FRAME_DELAY)

            boss_norm_min = float(self.boss.norm_hp)
            player_norm_min = float(self.player.norm_hp)
        
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

            cur = self.player.animation
            healing_now = cur in ANIMATIONS.HEAL
            healing_prev = self.prev_animation in ANIMATIONS.HEAL if self.prev_animation is not None else False

            if healing_now and not healing_prev and self.estus > 0:
                self.estus -= 1

            self.prev_animation = cur

            obs = self._get_observation()
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
            obs = self._get_observation()

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
            # refresh failed (game likely mid-transition); retry with delay
            for attempt in range(10):
                time.sleep(2)
                try:
                    self.ds3.attach()
                    self.ds3.refresh()
                    self.player = self.ds3.player
                    self.boss = self.ds3.boss
                    self.needs_refresh = False
                    break
                except (MemoryReadError, pymem.exception.WinAPIError, RuntimeError) as e:
                    print(f"refresh retry {attempt+1}/10 failed: {e}")
            else:
                raise RuntimeError("Could not refresh DS3 memory after 10 retries")
        controller.keep_ds3_alive()
        
        # Release all keys first to ensure clean state
        controller.release_all_keys()
        time.sleep(1)
        
        try:
            boss_hp = self.boss.hp if self.boss else 1
        except Exception:
            boss_hp = 0
        if boss_hp <= 0:
            self._wait_until_teleported()
            self._wait_until_loaded()
            controller.boss_died_reset()
            time.sleep(10)
        self.ep_boss_dmg = 0.0
        self.ep_player_dmg = 0.0

        self.estus = 3
        self.prev_animation = None
        self._wait_until_loaded()
        self._reset_mem()
        
        self.prev_player_hp = float(self.player.hp)
        self.prev_boss_hp = float(self.boss.hp)

        for walk_attempt in range(3):
            print(f"Walking to boss... (attempt {walk_attempt + 1})")
            open.focus_window("DARK SOULS III")
            time.sleep(2)
            controller.walk_to_boss()

            # Fog gate crossing changes lock_tgt_man in memory.
            # Re-initialize AFTER crossing so _locked_on_addr is valid for the boss arena.
            # Without this, every step() sees locked_on=False and calls turn_lock_on(),
            # spinning the camera and causing the agent to orbit the boss.
            time.sleep(0.5 / self.SPEED)
            self._reset_mem()

            dist = self._safe_dist()
            if dist < self.MAX_DIST:
                print(f"In arena (dist={dist:.1f})")
                break
            print(f"Walk failed (dist={dist:.1f}), retrying...")
            controller.release_all_keys()

        self.step_count = 0
        self.boss_defeated = False

        print(f"Reset complete")
        obs = self._get_observation()
        info = {
            "player_hp": self.player.hp,
            "boss_hp": self.boss.hp
        }

        return obs, info


    def do_action(self, actions):
        move, act = int(actions[0]), int(actions[1])

        controller.release_all_keys()
        controller.keep_ds3_alive()

        x, y = self._MOVE_JOYSTICK[move]
        controller.set_movement(x, y)

        match act:
            case 0: controller.right_hand_light_attack()
            case 1: controller.dodge()   # joystick direction = dodge direction
            case 2: controller.heal()
            case 3: pass                 # hold movement only

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
        
    def _boss_anim_prog(self):
        """Progress through the boss's current animation [0, 1]."""
        try:
            return float(np.clip(self.boss.animation_prog, 0.0, 1.0))
        except Exception:
            return 0.0

    def _get_observation(self):
        """Get current observation as a flat 31-dim array."""
        norm_dist = float(np.clip(self._safe_dist() / self.MAX_DIST, 0.0, 1.0))

        player_norm_hp = float(self._safe_read(lambda: self.player.norm_hp, 0.0))
        player_norm_sp = float(self._safe_read(lambda: self.player.norm_sp, 0.0))
        boss_norm_hp   = float(self._safe_read(lambda: self.boss.norm_hp, 0.0))

        stats = np.array([
            player_norm_hp,
            player_norm_sp,
            boss_norm_hp,
            norm_dist,
            self._boss_anim_prog(),
        ], dtype=np.float32)

        player_anim = self._encode_player_anim(self._safe_animation(default=0) or 0)
        boss_anim   = self._encode_boss_anim(self._safe_read(lambda: self.boss.animation_str, ""))

        return np.concatenate([player_anim, boss_anim, stats])

    def _encode_player_anim(self, animation):
        encoding = np.zeros(shape=(5,), dtype=np.float32)
        if animation in ANIMATIONS.LIGHT_ATTACK:
            encoding[0] = 1
        elif animation in ANIMATIONS.HEAL:
            encoding[1] = 1
        elif animation in ANIMATIONS.DODGE:
            encoding[2] = 1
        elif animation in ANIMATIONS.MOVE or animation in ANIMATIONS.IDLE:
            encoding[3] = 1
        else:
            encoding[4] = 1
        return encoding

    
    def _encode_boss_anim(self, animation_str):
        encoding = np.zeros(shape=(21,), dtype=np.float32);
        if animation_str in GUNDYR_ONE_HOT_ANIM:
            anim = GUNDYR_ONE_HOT_ANIM[animation_str]
        else:
            anim = 20
        encoding[anim] = 1
        return encoding
    
    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp, player_norm_min, boss_norm_min, action):
        a = np.asarray(action).squeeze()
        if a.shape == (2,):
            move, act = int(a[0]), int(a[1])
        else:
            # fallback if something weird happens
            act = int(np.asarray(action).ravel()[-1])

        reward = 0.0
        
        boss_damage = prev_boss_norm_hp - self.boss.norm_hp
        player_damage = prev_player_norm_hp - self.player.norm_hp

        reward += boss_damage * 10
        reward -= player_damage * 8

        dist = self._safe_dist()
        if dist < 3.5:
            reward += 0.05
        elif dist > 8.0:
            reward -= 0.02

        if act == 2 and self.estus == 0:
            reward -= 0.5

        if self.boss.hp <= 0:
            reward += 5

        if self.boss.norm_hp < 0.5:
            reward += 0.01

        if self.player.hp <= 0:
            reward -= 5

        if self.player.sp <= 15:
            reward -= 0.01

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
