from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback

import torch

from datetime import datetime
from ppov2 import DS3Env

env = DS3Env()
env = Monitor(env)
env = DummyVecEnv([lambda: env])
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
 
model = PPO(
    "MultiInputPolicy", 
    env, 
    policy_kwargs=policy_kwargs,
    verbose=1, 
    n_steps=1024,
    device="cuda",
    tensorboard_log="./ppo_ds3_logs"
)

try:
    print("Begin training")
    model.learn(1_000_000, callback=checkpoint)
except KeyboardInterrupt:
    print("Training cancelled...")
    model.save(f"./models/{datetime.now().strftime('%Y-%m-%d@%H:%M')}")
