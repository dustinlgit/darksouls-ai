from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure
from envs.no_img.env_early import DS3Env as envEarly
import numpy as np

EPISODES = 50


def make_env():
    env = envEarly()
    env = Monitor(env)  
    return env


env = DummyVecEnv([make_env])
env = VecFrameStack(env, n_stack=4, channels_order="last")

logger = configure("./eval_logs", ["stdout", "tensorboard"])
model = PPO.load("./models/early", env=env, device="cpu")
model.set_logger(logger)

wins = 0
boss_hps = []
player_hps = []
ttks = []

obs = env.reset()

print("--- Begin Testing ---")
for episode in range(EPISODES):
    done = [False]
    steps = 0

    while not done[0]:
        action, _ = model.predict(obs, deterministic=False)
        obs, reward, done, info = env.step(action)
        steps += 1

    ep_info = info[0]
    boss_hp = ep_info.get("boss_hp", 0)
    player_hp = ep_info.get("player_hp", 0)
    succ = ep_info.get("is_success", False)

    wins += int(succ)
    boss_hps.append(boss_hp)

    model.logger.record("eval/episode_boss_hp", boss_hp)

    if succ:
        ttks.append(steps)
        player_hps.append(player_hp)
        model.logger.record("eval/win_player_hp", player_hp)
        model.logger.record("eval/win_ttk", steps)

    model.logger.dump(step=episode)

    print(f"Episode {episode + 1:>3}/{EPISODES} | "
          f"{'WIN ' if succ else 'LOSS'} | "
          f"Steps: {steps:>5} | "
          f"Boss HP: {boss_hp:.1f} | "
          f"Player HP: {player_hp:.1f}")

success_rate  = wins / EPISODES
avg_ttk = np.mean(ttks) if ttks else 0.0
avg_boss_hp = np.mean(boss_hps) if boss_hps else 0.0
avg_player_hp = np.mean(player_hps) if player_hps else 0.0
med_boss_hp = np.median(boss_hps) if boss_hps else 0.0
med_player_hp = np.median(player_hps) if player_hps else 0.0 

model.logger.record("test/success_rate", success_rate)
model.logger.record("test/avg_boss_hp_remaining", avg_boss_hp)
model.logger.record("test/avg_player_hp_remaining", avg_player_hp)
model.logger.record("test/med_boss_hp_remaining", med_boss_hp)
model.logger.record("test/med_player_hp_remaining", med_player_hp) 
model.logger.record("test/avg_win_ttk", avg_ttk)
model.logger.dump(step=EPISODES)

print("-" * 30)
print(f"Success Rate: {success_rate:.2%}  ({wins}/{EPISODES})")
print(f"Avg Boss HP Remaining: {avg_boss_hp:.1f}")
print(f"Med Boss HP Remaining: {med_boss_hp:.1f}")
print(f"Avg Player HP (wins): {avg_player_hp:.1f}")
print(f"Avg Time to Kill: {avg_ttk:.1f} steps")

env.close()