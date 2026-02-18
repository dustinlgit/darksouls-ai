import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from collections import deque
import random

class ActorCritic(nn.Module):
    """Actor-Critic network for PPO"""
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(ActorCritic, self).__init__()
        
        # CNN for processing frames
        self.conv1 = nn.Conv2d(3, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        
        # Calculate conv output size (for 400x400 input)
        # After conv1: (400-8)/4+1 = 99
        # After conv2: (99-4)/2+1 = 48
        # After conv3: (48-3)/1+1 = 46
        conv_out_size = 64 * 46 * 46
        
        # Combine stats and frame features
        combined_size = conv_out_size + state_dim
        
        # Shared layers
        self.fc1 = nn.Linear(combined_size, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Actor head (policy)
        self.actor = nn.Linear(hidden_dim, action_dim)
        
        # Critic head (value)
        self.critic = nn.Linear(hidden_dim, 1)
        
    def forward(self, stats, frame):
        # Process frame through CNN
        frame = frame.float() / 255.0  # Normalize to [0, 1]
        x = F.relu(self.conv1(frame))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        #x = x.view(x.size(0), -1)  # Flatten #i changed this
        x = x.reshape(x.size(0), -1)
        
        # Combine with stats
        combined = torch.cat([x, stats], dim=1)
        
        # Shared layers
        x = F.relu(self.fc1(combined))
        x = F.relu(self.fc2(x))
        
        # Actor and Critic outputs
        action_probs = F.softmax(self.actor(x), dim=-1)
        value = self.critic(x)
        
        return action_probs, value

class PPOAgent:
    """PPO Agent implementation"""
    def __init__(
        self,
        state_dim=4,  # stats dimension
        action_dim=10,
        lr=1e-4,
        gamma=0.99,
        eps_clip=0.2,
        k_epochs=10,
        hidden_dim=256,
        device=None,
        target_kl=0.03
    ):
        self.target_kl = target_kl
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.k_epochs = k_epochs
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        print(f"Using device: {self.device}")
        
        # Initialize network
        self.policy = ActorCritic(state_dim, action_dim, hidden_dim).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        
        # Experience buffer
        self.reset_buffer()
        
    def reset_buffer(self):
        """Reset experience buffer"""
        self.states_stats = []
        self.states_frames = []
        self.actions = []
        self.rewards = []
        self.is_terminals = []
        self.log_probs = []
        
    def select_action(self, obs, deterministic=False):
        """Select action from observation"""
        stats = torch.FloatTensor(obs['stats']).unsqueeze(0).to(self.device)
        frame = torch.FloatTensor(obs['frame']).permute(2, 0, 1).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs, value = self.policy(stats, frame)
            
        if deterministic:
            action = torch.argmax(action_probs, dim=1).item()
        else:
            dist = torch.distributions.Categorical(action_probs)
            action = dist.sample().item()
            log_prob = dist.log_prob(torch.tensor(action))
            self.log_probs.append(log_prob)
        
        return action
    
    def store_transition(self, obs, action, reward, is_terminal):
        """Store transition in buffer"""
        self.states_stats.append(obs['stats'])
        self.states_frames.append(obs['frame'])
        self.actions.append(action)
        self.rewards.append(reward)
        self.is_terminals.append(is_terminal)
    
    def compute_returns(self, rewards, is_terminals, next_value=0):
        """Compute discounted returns"""
        returns = []
        G = next_value
        for reward, is_terminal in zip(reversed(rewards), reversed(is_terminals)):
            if is_terminal:
                G = 0
            G = reward + self.gamma * G
            returns.insert(0, G)
        return returns
    
    def update(self):
        """Update policy using PPO"""
        if len(self.states_stats) == 0:
            return {
                'actor_loss': 0.0,
                'critic_loss': 0.0,
                'entropy': 0.0,
                'mean_return': 0.0
            }
        
        # Convert to tensors
        old_states_stats = torch.FloatTensor(np.array(self.states_stats)).to(self.device)
        old_states_frames = torch.FloatTensor(np.array(self.states_frames)).permute(0, 3, 1, 2).to(self.device)
        old_actions = torch.LongTensor(self.actions).to(self.device)
        old_log_probs = torch.stack(self.log_probs).to(self.device)
        
        # Compute returns
        rewards = self.rewards
        is_terminals = self.is_terminals
        
        # Get next value estimate (for non-terminal last state)
        with torch.no_grad():
            if not is_terminals[-1]:
                _, next_value = self.policy(
                    old_states_stats[-1:],
                    old_states_frames[-1:]
                )
                next_value = next_value.item()
            else:
                next_value = 0
        
        returns = self.compute_returns(rewards, is_terminals, next_value)
        returns = torch.FloatTensor(returns).to(self.device)
        
        # Normalize returns with more stability
        returns_mean = returns.mean()
        returns_std = returns.std()
        if returns_std < 1e-8:
            returns_std = 1e-8
        returns = (returns - returns_mean) / returns_std
        
        # Get old values
        with torch.no_grad():
            _, old_values = self.policy(old_states_stats, old_states_frames)
            old_values = old_values.squeeze()
            # Ensure old_values has same shape as returns
            if old_values.dim() == 0:
                old_values = old_values.unsqueeze(0)
        
        advantages = returns - old_values
        
        # PPO update
        for _ in range(self.k_epochs):
            # Get current policy
            action_probs, values = self.policy(old_states_stats, old_states_frames)
            values = values.squeeze()
            # Ensure values has same shape as returns
            if values.dim() == 0:
                values = values.unsqueeze(0)
            
            # Ensure action_probs are valid (no NaN)
            if torch.isnan(action_probs).any():
                print("Warning: NaN detected in action_probs, skipping update")
                self.reset_buffer()
                return {
                    'actor_loss': 0.0,
                    'critic_loss': 0.0,
                    'entropy': 0.0,
                    'mean_return': 0.0
                }
            
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(old_actions)
            entropy = dist.entropy().mean()
            
            # Compute ratio
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # Compute surrogate losses
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantages
            
            # Actor loss
            actor_loss = -torch.min(surr1, surr2).mean()
            
            # Critic loss
            critic_loss = F.mse_loss(values, returns)
            
            # Total loss
            loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy
            
            # Update
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
            self.optimizer.step()
        
        # Reset buffer
        self.reset_buffer()
        
        return {
            'actor_loss': actor_loss.item(),
            'critic_loss': critic_loss.item(),
            'entropy': entropy.item(),
            'mean_return': returns.mean().item()
        }
    
    def save(self, filepath):
        """Save model"""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, filepath)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """Load model"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"Model loaded from {filepath}")
