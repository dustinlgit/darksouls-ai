---
layout: default
title: Proposal
---

## Summary of the Project

The objective of this project is to design an AI agent capable of defeating boss enemies in the action role playing game Dark Souls III. The agent operates in a fast paced combat setting that requires precise reactions, resource management, and adaptation to complex boss behaviors, and it is trained using the Dreamer reinforcement learning framework.

The AI receives visual input from the game in the form of screen captures, which include information such as player and boss health, stamina levels, and spatial relationships. Based on these observations, the agent outputs in game control actions, including movement, attacks, and evasive maneuvers, with the goal of winning boss encounters.

This project aims to explore whether a learning based agent can acquire effective combat strategies directly from visual observations and potentially serve as a tool for analyzing and understanding optimal boss fight strategies in action role playing games. 

## Project Goal

Our Minimum Goal: To defeat random mobs, in the game.

Our Realistic Goal: To defeat one boss.

Our Moonshot Goal: To defeat all bosses in the game. 

## AI/ML Algorithms

Our agent will be primarily trained using DreamerV3, a model-based off-policy reinforcement learning method. A potential method for sake of comparison and or fallback is PPO (proximal policy optimization), a model-free on-policy algorithm.

## Evaluation Plan

We first want to be able to see if we can even collect data ranging from player movement, boss movement, health, and other stats from the game and somehow fuse that with Dreamer to help with our reinforcement learning. We would want to identify rewards, and cost of rewards somehow, by combining these stats. 

If the data is too hard to obtain and parse, since there are so many variables to take in, we might have to shift gears to trying to use PPO instead of Dreamer, since that has been done before. And, worst case scenario, we might even switch games, to see if another one will be easier to work with in data collection. 

## AI Tool Usage

We plan to use AI for debugging and optimizing our code. 