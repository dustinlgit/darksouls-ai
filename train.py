from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.callbacks import EvalCallback

from collections import deque
import numpy as np
import torch
import os
import argparse

from datetime import datetime
from ppov2 import DS3Env

def make_env():
    env = DS3Env()
    env = Monitor(env)
    return env

parser = argparse.ArgumentParser(description="DS3 Agent Trainer")
parser.add_argument("--steps", type=int, default=100_000)
parser.add_argument("--load", type=str, help="Provide a path to the model")
args = parser.parse_args()


env = DummyVecEnv([make_env])
env = VecFrameStack(env, n_stack=4, channels_order="last")


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
    model = PPO.load(args.load, env=env, device="cpu")
else: 
    model = PPO(
        "MlpPolicy", 
        env, 
        policy_kwargs=policy_kwargs,
        verbose=1, 
        n_steps=1024,
        learning_rate=1e-4,
        gamma=0.995,
        gae_lambda=0.925,
        n_epochs=5,
        ent_coef=0.01,
        device="cpu",
        tensorboard_log="./logs"
    )

eval_cb = EvalCallback(
    env,
    best_model_save_path="./models/best_eval",
    log_path="./models/eval_logs",
    eval_freq=10_000,
    n_eval_episodes=5,
    deterministic=True,
    render=False
)

class winRate(BaseCallback):
    def __init__(self, window_size=100, check_freq=2000, save_path="./models/best_winrate", verbose=1):
        super().__init__(verbose)
        self.window_size = window_size
        self.check_freq = check_freq
        self.save_path = save_path
        self.win_buffer = deque(maxlen=window_size)
        self.best_win_rate = 0.0
        os.makedirs(save_path, exist_ok=True)

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", [])

        # update wins
        for info, done in zip(infos, dones):
            if done:
                win = 1 if info.get("is_success", False) else 0
                self.win_buffer.append(win)

        # periodically evaluate win rate
        if self.n_calls % self.check_freq == 0 and len(self.win_buffer) > 0:
            win_rate = float(np.mean(self.win_buffer))
            self.logger.record("rollout/win_rate_window", win_rate)
            self.logger.record("rollout/best_win_rate", self.best_win_rate)

            if win_rate > self.best_win_rate:
                self.best_win_rate = win_rate
                path = os.path.join(self.save_path, "best_model_by_winrate")
                self.model.save(path)
                if self.verbose:
                    print(f"[SAVE] New best win rate ({win_rate:.3f}) → {path}.zip")

        return True

try:
    print("Begin training")
    win_cb = winRate(window_size=100)

    model.learn(args.steps, callback=[checkpoint, eval_cb, win_cb], reset_num_timesteps=False)
except KeyboardInterrupt:
    print("Training cancelled...")
    model.save(f"./models/{datetime.now().strftime('%Y-%m-%d-%H-%M')}")
