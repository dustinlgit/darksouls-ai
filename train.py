from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack, VecTransposeImage
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback, EvalCallback

from collections import deque
import numpy as np
import torch
import os
import re
import argparse
from datetime import datetime

from ppov2 import DS3Env
from ppov2 import open


TB_ROOT = "./ppo_ds3_logs"
TB_RUN_NAME = "PPO_continuousv1"

def extract_steps_from_path(path: str) -> int | None:
    """
    Tries to extract a timestep count from common checkpoint names:
    - rl_model_300000_steps.zip
    - rl_model_300000.zip
    - model_300000.zip
    """
    base = os.path.basename(path)
    m = re.search(r"(\d+)", base)
    if not m:
        return None
    try:
        return int(m.group(1))
    except:
        return None


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
    "net_arch": {"pi": [128, 128], "vf": [128, 128]},
    "activation_fn": torch.nn.ReLU
}

checkpoint = CheckpointCallback(
    save_freq=4096,
    save_path="./models",
)

if args.load:
    # IMPORTANT: pass tensorboard_log here so SB3 continues logging into same root
    model = PPO.load(args.load, env=env, tensorboard_log=TB_ROOT)

    # Strongly recommended: continue the timestep axis if we can infer it
    inferred = extract_steps_from_path(args.load)
    if inferred is not None:
        model.num_timesteps = inferred
        model._last_obs = None  # avoids occasional stale obs issues after load (safe)
else:
    model = PPO(
        "MultiInputPolicy",
        env,
        policy_kwargs=policy_kwargs,
        verbose=1,
        n_steps=1024,
        device="cuda",
        tensorboard_log=TB_ROOT
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

        model.learn(
            total_timesteps=args.steps,
            callback=[checkpoint, eval_cb, EpisodeStatsCallback()],
            tb_log_name=TB_RUN_NAME,         # <-- fixed run folder name
            reset_num_timesteps=False        # <-- keep x-axis continuous
        )
        break

    except Exception as e:
        print("Training cancelled...", e)

        # If your process continues, keep training continuous by NOT resetting timesteps.
        # Save a crash checkpoint with the current num_timesteps so you can resume cleanly.
        crash_path = f"./models/crash_{model.num_timesteps}_{datetime.now().strftime('%Y-%m-%d@%H-%M')}"
        model.save(crash_path)

        open.enter_game()