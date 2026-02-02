"""
Main training script for Dark Souls III PPO agent
"""
import numpy as np
import time
from ppo import ds3Env
from ppo_agent import PPOAgent
import matplotlib.pyplot as plt
from collections import deque
import os

def train_ppo(
    num_episodes=1000,
    max_steps_per_episode=10000,
    update_frequency=2048,  # Update every N steps
    save_frequency=50,  # Save model every N episodes
    model_save_path="models/ppo_ds3",
    log_frequency=10
):
    """Train PPO agent on Dark Souls III environment"""
    
    # Create environment
    print("Initializing environment...")
    env = ds3Env()
    
    # Create agent
    print("Initializing PPO agent...")
    agent = PPOAgent(
        state_dim=4,
        action_dim=11,
        lr=3e-4,
        gamma=0.99,
        eps_clip=0.2,
        k_epochs=10
    )
    
    # Create model directory
    os.makedirs("models", exist_ok=True)
    
    # Training statistics
    episode_rewards = []
    episode_lengths = []
    episode_wins = []
    recent_rewards = deque(maxlen=100)
    recent_lengths = deque(maxlen=100)
    recent_wins = deque(maxlen=100)
    
    total_steps = 0
    best_reward = float('-inf')
    
    print("\nStarting training...")
    print("=" * 60)
    
    try:
        for episode in range(num_episodes):
            obs, info = env.reset()
            episode_reward = 0
            episode_length = 0
            episode_win = False
            
            # Run episode
            for step in range(max_steps_per_episode):
                # Select action
                action = agent.select_action(obs)
                
                # Take step
                next_obs, reward, terminated, truncated, step_info = env.step(action)
                
                # Store transition
                is_terminal = terminated or truncated
                agent.store_transition(obs, action, reward, is_terminal)
                
                episode_reward += reward
                episode_length += 1
                total_steps += 1
                
                # Check if episode ended
                if terminated or truncated:
                    if step_info.get('boss_hp', 1) <= 0:
                        episode_win = True
                    break
                
                obs = next_obs
                
                # Update agent periodically
                if len(agent.states_stats) >= update_frequency:
                    update_info = agent.update()
                    if episode % log_frequency == 0:
                        print(f"  Update - Actor Loss: {update_info['actor_loss']:.4f}, "
                              f"Critic Loss: {update_info['critic_loss']:.4f}, "
                              f"Entropy: {update_info['entropy']:.4f}")
            
            # Final update if buffer has data
            if len(agent.states_stats) > 0:
                update_info = agent.update()
            
            # Record statistics
            episode_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
            episode_wins.append(1 if episode_win else 0)
            recent_rewards.append(episode_reward)
            recent_lengths.append(episode_length)
            recent_wins.append(1 if episode_win else 0)
            
            # Print progress
            if episode % log_frequency == 0:
                avg_reward = np.mean(recent_rewards) if recent_rewards else 0
                avg_length = np.mean(recent_lengths) if recent_lengths else 0
                win_rate = np.mean(recent_wins) if recent_wins else 0
                
                print(f"\nEpisode {episode}/{num_episodes}")
                print(f"  Reward: {episode_reward:.2f} (Avg: {avg_reward:.2f})")
                print(f"  Length: {episode_length} (Avg: {avg_length:.1f})")
                print(f"  Win: {'Yes' if episode_win else 'No'} (Rate: {win_rate*100:.1f}%)")
                print(f"  Total Steps: {total_steps}")
                print(f"  Player HP: {step_info.get('player_hp', 'N/A')}, "
                      f"Boss HP: {step_info.get('boss_hp', 'N/A')}")
                print("-" * 60)
            
            # Save model
            if episode % save_frequency == 0 and episode > 0:
                agent.save(f"{model_save_path}_ep{episode}.pth")
                if episode_reward > best_reward:
                    best_reward = episode_reward
                    agent.save(f"{model_save_path}_best.pth")
                    print(f"  Saved best model (reward: {best_reward:.2f})")
            
            # Early stopping if consistently winning
            if len(recent_wins) >= 50 and np.mean(list(recent_wins)[-50:]) >= 0.9:
                print(f"\nAgent is consistently winning! Stopping training.")
                break
    
    except KeyboardInterrupt:
        print("\nTraining interrupted by user.")
    
    finally:
        # Save final model
        agent.save(f"{model_save_path}_final.pth")
        
        # Plot training curves
        plot_training_curves(episode_rewards, episode_lengths, episode_wins)
        
        print("\nTraining completed!")
        print(f"Final statistics:")
        print(f"  Total Episodes: {len(episode_rewards)}")
        print(f"  Average Reward: {np.mean(episode_rewards):.2f}")
        print(f"  Average Length: {np.mean(episode_lengths):.1f}")
        print(f"  Win Rate: {np.mean(episode_wins)*100:.1f}%")
        print(f"  Best Reward: {best_reward:.2f}")

def plot_training_curves(rewards, lengths, wins):
    """Plot training statistics"""
    try:
        fig, axes = plt.subplots(3, 1, figsize=(10, 12))
        
        # Rewards
        axes[0].plot(rewards, alpha=0.3, color='blue')
        if len(rewards) >= 100:
            moving_avg = np.convolve(rewards, np.ones(100)/100, mode='valid')
            axes[0].plot(range(99, len(rewards)), moving_avg, color='red', linewidth=2, label='Moving Average (100)')
        axes[0].set_xlabel('Episode')
        axes[0].set_ylabel('Reward')
        axes[0].set_title('Episode Rewards')
        axes[0].legend()
        axes[0].grid(True)
        
        # Episode lengths
        axes[1].plot(lengths, alpha=0.3, color='green')
        if len(lengths) >= 100:
            moving_avg = np.convolve(lengths, np.ones(100)/100, mode='valid')
            axes[1].plot(range(99, len(lengths)), moving_avg, color='red', linewidth=2, label='Moving Average (100)')
        axes[1].set_xlabel('Episode')
        axes[1].set_ylabel('Steps')
        axes[1].set_title('Episode Lengths')
        axes[1].legend()
        axes[1].grid(True)
        
        # Win rate
        if len(wins) >= 100:
            win_rate = np.convolve(wins, np.ones(100)/100, mode='valid')
            axes[2].plot(range(99, len(wins)), win_rate, color='purple', linewidth=2)
        else:
            win_rate = np.cumsum(wins) / (np.arange(len(wins)) + 1)
            axes[2].plot(win_rate, color='purple', linewidth=2)
        axes[2].set_xlabel('Episode')
        axes[2].set_ylabel('Win Rate')
        axes[2].set_title('Win Rate (Moving Average)')
        axes[2].set_ylim([0, 1])
        axes[2].grid(True)
        
        plt.tight_layout()
        plt.savefig('training_curves.png')
        print("Training curves saved to training_curves.png")
        plt.close()
    except Exception as e:
        print(f"Could not plot training curves: {e}")

def test_agent(model_path, num_episodes=5):
    """Test trained agent"""
    print(f"\nTesting agent from {model_path}...")
    
    env = ds3Env()
    agent = PPOAgent(state_dim=4, action_dim=11)
    agent.load(model_path)
    
    wins = 0
    total_rewards = []
    
    for episode in range(num_episodes):
        obs, info = env.reset()
        episode_reward = 0
        episode_win = False
        
        for step in range(10000):
            action = agent.select_action(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            
            if terminated or truncated:
                if info.get('boss_hp', 1) <= 0:
                    episode_win = True
                    wins += 1
                break
        
        total_rewards.append(episode_reward)
        print(f"Episode {episode+1}: Reward={episode_reward:.2f}, Win={'Yes' if episode_win else 'No'}")
    
    print(f"\nTest Results:")
    print(f"  Win Rate: {wins/num_episodes*100:.1f}%")
    print(f"  Average Reward: {np.mean(total_rewards):.2f}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train PPO agent on Dark Souls III')
    parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    parser.add_argument('--update-freq', type=int, default=2048, help='Update frequency (steps)')
    parser.add_argument('--save-freq', type=int, default=50, help='Save frequency (episodes)')
    parser.add_argument('--model-path', type=str, default='models/ppo_ds3', help='Model save path')
    parser.add_argument('--test', type=str, default=None, help='Test mode: path to model file')
    parser.add_argument('--test-episodes', type=int, default=5, help='Number of test episodes')
    
    args = parser.parse_args()
    
    if args.test:
        test_agent(args.test, args.test_episodes)
    else:
        train_ppo(
            num_episodes=args.episodes,
            update_frequency=args.update_freq,
            save_frequency=args.save_freq,
            model_save_path=args.model_path
        )
