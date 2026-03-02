import gymnasium as gym
from gymnasium import spaces

import numpy as np
import time
import math

from memory import DS3Reader, BOSSES, ANIMATIONS, GUNDYR_ONE_HOT_ANIM
import controller

class DS3Env(gym.Env):
    SPEED = 1
    MAX_DIST = 12
    FRAME_SKIP = 4
    FRAME_DELAY = FRAME_SKIP / 60 / SPEED

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
        self.action_space = spaces.MultiDiscrete([5, 4])
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(30,), dtype=np.float32)

        self.heal_count = 0

    def _safe_dist(self):
        try:
            d = float(math.dist(self.player.pos, self.boss.pos))
        except Exception:
            return self.MAX_DIST
        if not np.isfinite(d):
            return self.MAX_DIST
        return d
    
    def step(self, action):
        try:
            prev_player_norm_hp = self.player.norm_hp
            prev_boss_norm_hp = self.boss.norm_hp
            
            controller.release_all()
            self.do_action(action)

            time.sleep(self.FRAME_DELAY)
            controller.release_all()

            cur = self.player.animation
            healing_now = cur in ANIMATIONS.HEAL
            healing_prev = self.prev_animation in ANIMATIONS.HEAL if self.prev_animation is not None else False

            if healing_now and not healing_prev and self.estus > 0:
                self.estus -= 1

            self.prev_animation = cur

            obs = self._get_observation()
            reward = self._calculate_reward(prev_player_norm_hp, prev_boss_norm_hp, action[1])
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
        except:
            controller.open.enter_game()
            self.step(action)
    

    def render(self):
        pass


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        controller.keep_ds3_alive()
        
        # Release all keys first to ensure clean state
        controller.release_all()
        time.sleep(1)
        
        if self.boss and self.boss.hp <= 0:
            self._wait_until_teleported()
            self._wait_until_loaded()
            controller.boss_died_reset()
            time.sleep(10)
        
        self._wait_until_loaded()
        self._reset_mem()
        print("SUCCCESS: _wait_until_loaded & _reset_mem")
        
        controller.walk_to_boss(self.SPEED)
        print("SUCCCESS: walk_to_boss")
        
        self.step_count = 0
        self.boss_defeated = False
        self.estus = 3
        self.prev_animation = None

        obs = self._get_observation()
        info = {
            "player_hp": self.player.hp,
            "boss_hp": self.boss.hp
        }
        print("SUCCCESS: _get_observation")

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
            case 4: 
                controller.move_neutral()
            case _: 
                controller.move_neutral()

        match act:
            case 0:
                controller.attack()
            case 1:
                controller.dodge()
            case 2:
                controller.heal()
            case 3:
                controller.no_action()
            case _: 
                controller.no_action()
        
        

    def _get_observation(self):
        """Get current observation (stats + frame)"""
        dist = self._safe_dist()
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

    

    def _calculate_reward(self, prev_player_norm_hp, prev_boss_norm_hp, action=3):
        """Calculate reward based on state changes"""
        reward = 0.0
        
        boss_damage = prev_boss_norm_hp - self.boss.norm_hp
        
        player_hp_change = self.player.norm_hp - prev_player_norm_hp

        dmg_taken = max(0.0, -player_hp_change)
        healing_done = max(0.0, player_hp_change)

        reward += boss_damage * 10
        reward -= dmg_taken * 8

        reward += healing_done * 1.0

        if action == 2 and self.estus == 0:
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
        self.heal_count = 0
        self.player = self.ds3.player
        self.boss = self.ds3.boss


    def _wait_until_teleported(self):
        try:
            while self.player.y < 600:
                self.ds3.initialize()
        except Exception as err:
            ... #print("_wait_until_teleported:", err)
        time.sleep(5)


    def _wait_until_loaded(self):
        while True:
            try:
                self.ds3.initialize()
                if self.ds3.player.animation in ANIMATIONS.IDLE:
                    break
            except Exception as err:
                ...#print("_wait_until_loaded:", err)
        time.sleep(1.5)
