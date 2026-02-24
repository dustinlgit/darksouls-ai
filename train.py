from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import VecFrameStack, VecTransposeImage

from collections import deque
import numpy as np
import torch
import os
import argparse

from datetime import datetime
from ppov2 import DS3Env
from ppov2 import open

def make_env():
    env = DS3Env()
    env = Monitor(env, info_keywords=("boss_dmg", "player_dmg", "is_success"))
    return env

parser = argparse.ArgumentParser(description="DS3 Agent Trainer")
parser.add_argument("--steps", type=int, default=100_000)
parser.add_argument("--load", type=str, help="Provide a path to the model")
args = parser.parse_args()


env = DummyVecEnv([make_env])
env = VecFrameStack(env, n_stack=4, channels_order="last")
env = VecTransposeImage(env)

policy_kwargs = {
    "net_arch": {
        "pi": [128, 128],
        "vf": [128, 128]
    },
    "activation_fn": torch.nn.ReLU
}

checkpoint = CheckpointCallback(
    save_freq=4096,
    save_path="./models",
)

if args.load:
    model = PPO.load(args.load, env=env)
else: 
    model = PPO(
        "MultiInputPolicy", 
        env, 
        policy_kwargs=policy_kwargs,
        verbose=1, 
        n_steps=1024,
        device="cuda",
        tensorboard_log="./ppo_ds3_logs"
    )

class EpisodeStatsCallback(BaseCallback):
    def __init__(self, window=100, verbose=0):
        super().__init__(verbose)
        self.window = window
        self.succ = deque(maxlen=window)
        self.boss = deque(maxlen=window)
        self.pdmg = deque(maxlen=window)

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            if "episode" in info:
                ep = info["episode"]
                self.succ.append(ep.get("is_success", 0.0))
                self.boss.append(ep.get("boss_dmg", 0.0))
                self.pdmg.append(ep.get("player_dmg", 0.0))

                self.logger.record("roll/success_rate", float(np.mean(self.succ)))
                self.logger.record("roll/boss_dmg_mean", float(np.mean(self.boss)))
                self.logger.record("roll/player_dmg_mean", float(np.mean(self.pdmg)))
        return True
    
eval_env = DummyVecEnv([make_env])
eval_env = VecFrameStack(eval_env, n_stack=4, channels_order="last")
eval_env = VecTransposeImage(eval_env)
eval_cb = EvalCallback(
    eval_env,
    best_model_save_path="./models/best_eval",
    log_path="./models/eval_logs",
    eval_freq=10_000,
    n_eval_episodes=20,
    deterministic=True,
    render=False
)
while True:
    try:
        print("Begin training")
        model.learn(args.steps, callback=[checkpoint, eval_cb, EpisodeStatsCallback()])
        break
    except Exception as e:
        print("Training cancelled...", e)
        open.enter_game()
        model.save(f"./models/{datetime.now().strftime('%Y-%m-%d@%H:%M')}")
