from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3.common.monitor import Monitor

import torch

from ppov3 import DS3Env

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

model = PPO(
    "MultiInputPolicy", 
    env, 
    policy_kwargs=policy_kwargs,
    verbose=1, 
    n_steps=1024,
    device="cuda",
    tensorboard_log="./ppo_ds3_logs"
)

model.learn(total_timesteps=100_000)