---
layout: default
title: Status
---

## Project Summary

This project develops a reinforcement learning agent capable of fighting the first boss in *Dark Souls III* using Proximal Policy Optimization (PPO). The agent interacts with the live game by combining data read from memory (e.g., player health, stamina, boss health, positional data) with raw screen pixel observations. Actions are executed through simulated controller inputs, allowing the model to perform attacks, dodges, movement, and healing in real time. The goal is to learn a combat policy that maximizes survivability and boss damage without relying on scripted logic. By training from scratch against Iudex Gundyr (the first boss), this project explores whether a model-free policy-gradient method can learn adaptive, timing-sensitive combat strategies in a high-difficulty, partially observable 3D environment.

## Approach

We formulate the boss fight as a reinforcement learning problem and train an agent using Proximal Policy Optimization (PPO). PPO is a policy-gradient method that improves training stability by optimizing a clipped surrogate objective rather than directly maximizing the raw policy gradient. The clipped objective constrains policy updates to remain close to the previous policy, preventing destructive updates that can destabilize training. The optimization objective includes a policy loss term, a value function loss for critic learning, and an entropy bonus to encourage exploration. We use the Stable-Baselines3 implementation of PPO and train the model from randomly initialized weights.

The environment is a gym environment, built as a custom interface to *Dark Souls III*. The agent interacts with the game by reading structured values directly from memory and capturing the game screen as image input. Memory features include player HP, player stamina, player animation, boss HP, and positional coordinates for both player and boss. From these values, we compute additional features such as relative distance between the player and the boss. These structured inputs provide clean, low-noise state information that would otherwise be difficult and computationally expensive for the model to infer from pixels alone.

In addition to memory features, the agent receives raw pixel observations captured from the game window. The frames are resized (128x128) and grayscaled, to cut down on unnecessary color noise, before being passed into a convolutional neural network (CNN). 

<figure style="text-align: center;">
    <img src="assets/example_frame.png" width=200>
    <figcaption>
        <small>
            <i>Figure 1: Downsized and grayscaled 128x128 frame capture</i>
        </small>
    </figcaption>
</figure>

The CNN extracts spatial features such as boss animation cues, attack windups, and environmental layout. The memory features are processed through a multilayer perceptron (MLP). The outputs of the CNN and MLP are concatenated into a shared latent representation that feeds into both the policy head and value head of the PPO architecture. This hybrid observation design allows the model to leverage both structured state information and visual context.

The action space is discrete (`Discrete(9)`), and each action triggers a predefined simulated sequence of (XBox360) controller inputs such as:
- No action
- Light attack
- Dodge
- Dodge roll
- Directional movement
- Use flask (healing)

The reward function is shaped to encourage effective combat behavior. The agent receives positive reward proportional to boss health reduction and a large terminal reward for defeating the boss. It receives negative reward for taking damage and a significant penalty for player death. As healing resources are limited per combat encounter, rewards for optimal usage (more HP healed), and penalties for inefficient usage are used. In addition, the relative distance between the player and boss is rewarded when small (in range to attck), and becomes punished if the agent moves too far away. This reward structure encourages aggressive but survivable strategies, balancing survival with reasonable damage output.


## Evaluation

The main metric of success for our project is the consistency of our agent in defeating a boss enemy (or enemies). In other words, we want to maximize the probability of successfully defeating a boss enemy per episode. Once our agent is able to consistently defeat a boss, we can optimize its behavior and various other metrics during combat. Other metrics will include damage taken, time taken, and reward metrics, per boss fight (episode). 

The baseline metrics will come from a policy that takes random actions or a basic policy manually weighted towards certain actions. Another baseline to consider is the performance of a human player who is new to the game. As *Dark Souls III* is a complex game, the baseline policies are expected to perform abysmally, so an expected increase of 20% (flat) boss defeat rate is expected. Compared to a new player, we expect a trained agent to perform 100% better (relative).

Qualitatively, as part of the Dreamer framework, the internals of the model will be tested in the real world environment (*Dark Souls III*). Sanity checking will include episodes being run with the current policy in the real environment. We can observe whether our agent has developed action patterns in response to the environment (boss enemy and current resources), or if the agent is randomly choosing actions. The agent dodging in response to enemy attacks and attacking the enemy when its vulnerable are qualitative signs of a successful policy. Debugging will be reliant on observing the agent's actions. If we observe behavior from the agent that is detrimental to their ability to defeat the enemy, we can do reward shaping to discourage it.

So far it has been difficult tweaking rewards. For example, we have trained for multiple days, using different ways to calculate rewards, and most of the time it starts to lean heavily towards wanting to do 1 certain action since it yields a high reward instead of just killing the boss. To be more specific, there have been times where I trained overnight, and woke up to see the agent rolling around, and healing a lot, instead of doing offensive actions. At the moment, some overnight runs yield a success (see figure above), meaning that our ai agent was able to defeat the boss, although this is good, we still struggle with attaining a model with a consistent success rate.


<figure style="text-align: center;">
    <img src="assets/qual_bad.gif">
    <figcaption>
        <small>
            <i>Figure 2: Poor qualitative performance</i>
        </small>
    </figcaption>
</figure>


An example of bad qualitative performance. The agent stays away from the boss, misses attacks (due to its distance), and mistimes dodge rolls, ending with the agent taking substantial damage while outputting none in return. This sort of bad qualitative performance is expected at the start of training, but as training moves forward, we use this visual qualitative analysis to shape the reward towards avoiding bad behavior. A common issue at the start was behavior similar to this short example even after training, which we were able to mitigate with different reward shaping.

## Remaining Goals and Challenges

So far it has been difficult tweaking rewards. For example, we have trained for multiple days, using different ways to calculate rewards, and most of the time it starts to lean heavily towards wanting to do 1 certain action since it yields a high reward instead of just killing the boss. To be more specific, there have been times where I trained overnight, and woke up to see the agent rolling around, and healing a lot, instead of doing offensive actions. At the moment, some overnight runs yield a success (see figure above), meaning that our ai agent was able to defeat the boss, although this is good, we still struggle with attaining a model with a consistent success rate.

For the remainder of the quarter, I want to try my best to get a model that has a high consistency rate of killing the boss. If there comes a time where my model isn’t able to enact high win rates, I would like to shift into training the model with infinite hp, and see how that changes the learning rate, and outcomes. Some challenges which I think will be persistent might be how the agent will overfit to certain actions, such as spam rolling, to avoid damage, instead of attacking. I also think that something that limits me is the fact I have to train overnight, and I cannot so easily adjust certain rewards right away. I have to wait various hours to then analyze what happened, and what I can fix to train the next night.

## Resources Used

##### Reinforcement Learning
- Stable-Baselines3 for the PPO implementation and training framework
- Gymnasium to build our custom *Dark Souls III* environment
- PyTorch for neural network computation and model architecture
- Official Stable-Baselines3 and PyTorch documentation for hyperparameter configuration and architecture setup
- Online reinforcement learning resources and PPO research discussions for understanding the clipped objective and generalized advantage estimation
- StackOverflow and technical forums for debugging implementation and environment-integration issues

##### Interface and Environment Utilities
- [pymem](https://pypi.org/project/Pymem/) for reading structured game state values directly from *Dark Souls III* memory
- [The Grand Archives](https://github.com/The-Grand-Archives/Dark-Souls-III-CT-TGA) for providing a foundation for memory data extraction
- [vgamepad](https://github.com/yannbouteiller/vgamepad) (virtual XBox360 controller), which utilizes [ViGEmBus](https://github.com/nefarius/ViGEmBus), for executing agent actions
- [mss](https://pypi.org/project/mss/) for capturing images
- [Boss Arena](https://www.nexusmods.com/darksouls3/mods/1854) mod for *Dark Souls III*, which enables rapid access to the boss encounter and significantly reduces reset time between episodes, improving training efficiency and experimental control

##### AI Usage
- AI tools (including ChatGPT) for
- clarifying PPO theory and debugging conceptual reinforcement learning issues
- refining reward design
- improving report clarity
- debugging codebase

## Video Summary