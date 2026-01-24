---
layout: default
title: Proposal
---

## Summary of the Project

The objective of this project is to design an AI agent capable of defeating boss enemies in the action role playing game Dark Souls III. The agent operates in a fast paced combat setting that requires precise reactions, resource management, and adaptation to complex boss behaviors, and it is trained using the Dreamer reinforcement learning framework.

The AI receives visual input from the game in the form of screen captures, which include information such as player and boss health, stamina levels, and spatial relationships. Based on these observations, the agent outputs in game control actions, including movement, attacks, and evasive maneuvers, with the goal of winning boss encounters.

This project aims to explore whether a learning based agent can acquire effective combat strategies directly from visual observations and potentially serve as a tool for analyzing and understanding optimal boss fight strategies in action role playing games. 

## Project Goal

Our Minimum Goal: The agent learns to defeat a boss enemy a single time.

Our Realistic Goal: The agent learns to defeat one boss enemy more consistently and optimally (less resources used, e.g., less damage taken, less healing used, worse player stats).

Our Moonshot Goal: The agent is able to defeat all boss enemies.

## AI/ML Algorithms

Our agent will be primarily trained using DreamerV3, a model-based off-policy reinforcement learning method. A potential method for sake of comparison and or fallback is PPO (proximal policy optimization), a model-free on-policy algorithm.

## Evaluation Plan

The main metric of success for our project is the consistency of our agent in defeating a boss enemy (or enemies). In other words, we want to maximize the probability of successfully defeating a boss enemy per episode. Once our agent is able to consistently defeat a boss, we can optimize its behavior and various other metrics during combat. Other metrics will include damage taken, time taken, and reward metrics, per boss fight (episode). 

The baseline metrics will come from a policy that takes random actions or a basic policy manually weighted towards certain actions. Another baseline to consider is the performance of a human player who is new to the game. As Dark Souls III is a complex game, the baseline policies are expected to perform abysmally, so an expected increase of 20% (flat) boss defeat rate is expected. Compared to a new player, we expect a trained agent to perform 100% better (relative).

Qualitatively, as part of the Dreamer framework, the internals of the model will be tested in the real world environment (Dark Souls III). Sanity checking will include episodes being run with the current policy in the real environment. We can observe whether our agent has developed action patterns in response to the environment (boss enemy and current resources), or if the agent is randomly choosing actions. The agent dodging in response to enemy attacks and attacking the enemy when its vulnerable are qualitative signs of a successful policy. Debugging will be reliant on observing the agent's actions. If we observe behavior from the agent that is detrimental to their ability to defeat the enemy, we can do reward shaping to discourage it.

## AI Tool Usage

We plan to use AI for debugging and optimizing our code. 
