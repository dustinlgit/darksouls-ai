import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from collections import deque
import random

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256, in_channels=1, input_hw=128):
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)

        # compute conv output size dynamically
        with torch.no_grad():
            dummy = torch.zeros(1, in_channels, input_hw, input_hw)
            x = F.relu(self.conv1(dummy))
            x = F.relu(self.conv2(x))
            x = F.relu(self.conv3(x))
            conv_out_size = x.reshape(1, -1).shape[1]

        combined_size = conv_out_size + state_dim

        self.fc1 = nn.Linear(combined_size, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)

        self.actor = nn.Linear(hidden_dim, action_dim)
        self.critic = nn.Linear(hidden_dim, 1)

    def forward(self, stats, frame):
        frame = frame.float() / 255.0
        x = F.relu(self.conv1(frame))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.reshape(x.size(0), -1)

        combined = torch.cat([x, stats], dim=1)

        x = F.relu(self.fc1(combined))
        x = F.relu(self.fc2(x))

        logits = self.actor(x)                     # IMPORTANT: logits, not softmax
        value = self.critic(x)
        return logits, value

class PPOAgent:
    """PPO Agent implementation"""
    def __init__(
        self,
        state_dim=6,  # stats dimension
        action_dim=10,
        lr=1e-4,
        gamma=0.99,
        eps_clip=0.10,
        k_epochs=10,
        hidden_dim=256,
        device=None,
        target_kl=0.03,
        ent_coef=0.03
    ):
        self.ent_coef = ent_coef
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
        self.policy = ActorCritic(
            state_dim=6,
            action_dim=action_dim,
            hidden_dim=hidden_dim,
            in_channels=1,
            input_hw=128
        ).to(self.device)
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
        stats = torch.as_tensor(obs['stats'], dtype=torch.float32, device=self.device).unsqueeze(0)
        frame = torch.as_tensor(obs['frame'], dtype=torch.float32, device=self.device).permute(2, 0, 1).unsqueeze(0)

        with torch.no_grad():
            logits, _ = self.policy(stats, frame)

        dist = torch.distributions.Categorical(logits=logits)

        if deterministic:
            action = torch.argmax(logits, dim=1)
        else:
            action = dist.sample()

        log_prob = dist.log_prob(action)
        self.log_probs.append(log_prob.detach().cpu().view(()))  # store scalar

        return int(action.item())
    
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
        if len(self.states_stats) == 0:
            return {'actor_loss': 0.0, 'critic_loss': 0.0, 'entropy': 0.0, 'mean_return': 0.0}

        # Convert to tensors
        old_states_stats = torch.FloatTensor(np.array(self.states_stats)).to(self.device)
        old_states_frames = torch.FloatTensor(np.array(self.states_frames)).permute(0, 3, 1, 2).to(self.device)
        old_actions = torch.LongTensor(self.actions).to(self.device)

        # log_probs saved as cpu tensors; make 1D on device
        old_log_probs = torch.stack(self.log_probs).to(self.device).view(-1)

        T = old_states_stats.size(0)
        minibatch_size = min(256, T)

        # Compute bootstrap value for last state if not terminal
        with torch.no_grad():
            if not self.is_terminals[-1]:
                _, next_value = self.policy(old_states_stats[-1:], old_states_frames[-1:])
                next_value = next_value.item()
            else:
                next_value = 0.0

        # Returns (you can keep your normalize if you want)
        returns = self.compute_returns(self.rewards, self.is_terminals, next_value)
        returns = torch.FloatTensor(returns).to(self.device)

        # Value baseline
        with torch.no_grad():
            _, old_values = self.policy(old_states_stats, old_states_frames)
            old_values = old_values.squeeze()
            if old_values.dim() == 0:
                old_values = old_values.unsqueeze(0)

        # Advantages (detach + normalize)
        advantages = (returns - old_values).detach()
        adv_std = advantages.std()
        if adv_std < 1e-8:
            adv_std = 1e-8
        advantages = (advantages - advantages.mean()) / adv_std

        # (Optional but recommended) normalize returns for critic stability
        ret_std = returns.std()
        if ret_std < 1e-8:
            ret_std = 1e-8
        norm_returns = (returns - returns.mean()) / ret_std

        # PPO update
        actor_loss_val, critic_loss_val, entropy_val = 0.0, 0.0, 0.0

        for _ in range(self.k_epochs):
            idx = torch.randperm(T, device=self.device)

            # minibatch loop
            for start in range(0, T, minibatch_size):
                mb = idx[start:start + minibatch_size]

                action_probs, values = self.policy(old_states_stats[mb], old_states_frames[mb])
                values = values.squeeze()

                if torch.isnan(action_probs).any():
                    print("Warning: NaN detected in action_probs, skipping update")
                    self.reset_buffer()
                    return {'actor_loss': 0.0, 'critic_loss': 0.0, 'entropy': 0.0, 'mean_return': float(returns.mean().item())}

                dist = torch.distributions.Categorical(probs=action_probs)
                new_log_probs = dist.log_prob(old_actions[mb])
                entropy = dist.entropy().mean()

                # KL early stop (approx)
                with torch.no_grad():
                    approx_kl = (old_log_probs[mb] - new_log_probs).mean()
                if approx_kl > 1.5 * self.target_kl:
                    break

                ratio = torch.exp(new_log_probs - old_log_probs[mb])

                surr1 = ratio * advantages[mb]
                surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantages[mb]
                actor_loss = -torch.min(surr1, surr2).mean()

                critic_loss = F.mse_loss(values, norm_returns[mb])

                loss = actor_loss + 0.5 * critic_loss - self.ent_coef * entropy

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                self.optimizer.step()

                actor_loss_val = actor_loss.item()
                critic_loss_val = critic_loss.item()
                entropy_val = entropy.item()

        self.reset_buffer()

        return {
            'actor_loss': actor_loss_val,
            'critic_loss': critic_loss_val,
            'entropy': entropy_val,
            'mean_return': float(returns.mean().item())
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
