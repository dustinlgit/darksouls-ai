# Dark Souls III AI - PPO Agent

A reinforcement learning agent trained using Proximal Policy Optimization (PPO) to defeat bosses in Dark Souls III.

## Overview

This project implements a PPO-based AI agent that learns to play Dark Souls III by:
- Reading game state from memory (HP, stamina, boss HP)
- Capturing screen frames for visual input
- Executing actions (attacks, dodges, movement, etc.)
- Learning optimal strategies through reinforcement learning

## Features

- **Gymnasium Environment**: Custom `ds3Env` environment that interfaces with Dark Souls III
- **PPO Agent**: Actor-Critic network with CNN for frame processing
- **Memory Reading**: Direct memory access to read player and boss stats
- **Frame Capture**: Screen capture for visual observations
- **Action Execution**: 11 different actions including attacks, dodges, movement, and healing

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure Dark Souls III is running (or the Boss Arena mod)

## Usage

### Training

Train the agent:
```bash
python train_ppo.py --episodes 1000 --update-freq 2048 --save-freq 50
```

Arguments:
- `--episodes`: Number of training episodes (default: 1000)
- `--update-freq`: Steps between policy updates (default: 2048)
- `--save-freq`: Episodes between model saves (default: 50)
- `--model-path`: Path to save models (default: `models/ppo_ds3`)

### Testing

Test a trained model:
```bash
python train_ppo.py --test models/ppo_ds3_best.pth --test-episodes 5
```

## Architecture

### Environment (`ppo.py`)
- **Observation Space**: 
  - Stats: Normalized HP ratios, stamina ratio, boss HP ratio
  - Frame: 400x400 RGB image
- **Action Space**: 11 discrete actions
- **Rewards**: 
  - Positive for dealing damage to boss
  - Negative for taking damage
  - Large reward for defeating boss
  - Large penalty for dying

### PPO Agent (`ppo_agent.py`)
- **Actor-Critic Network**:
  - CNN layers for frame processing
  - Fully connected layers combining stats and frame features
  - Separate heads for policy (actor) and value (critic)
- **PPO Algorithm**:
  - Clipped surrogate objective
  - Value function learning
  - Entropy bonus for exploration

## Actions

The agent can perform 11 different actions:
0. No action (wait)
1. Right hand light attack
2. Forward run attack
3. Dodge
4. Forward roll dodge
5. Shield
6. Run forward
7. Run backward
8. Run right
9. Run left
10. Heal

## Training Tips

1. **Start with shorter episodes**: The agent needs to learn basic survival first
2. **Monitor win rate**: Track how often the agent defeats the boss
3. **Adjust rewards**: Modify reward function in `ppo.py` if needed
4. **Hyperparameters**: Adjust learning rate, gamma, and clip epsilon in `ppo_agent.py`

## Files

- `ppo.py`: Gymnasium environment for Dark Souls III
- `ppo_agent.py`: PPO agent implementation with Actor-Critic network
- `train_ppo.py`: Main training script
- `actions.py`: Game action functions
- `get_frame.py`: Screen capture utilities
- `memory/`: Memory reading utilities for game state

## Notes

- The agent requires Dark Souls III to be running
- Memory reading may need adjustment based on game version
- Frame capture requires the game window to be visible
- Training can take many hours depending on hardware

## Troubleshooting

**"Dark Souls not Found"**: Make sure the game is running and the window title is "DARK SOULS III"

**Memory reading errors**: The game process might not be accessible. Try running as administrator.

**Frame capture issues**: Ensure the game window is visible and not minimized.

## License

This project is for educational purposes.
