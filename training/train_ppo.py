"""
training/train_ppo.py
Reproducible PPO Training for Adaptive Edge-Compute Maritime Scheduler
Uses Gymnasium and Stable-Baselines3 PPO.
Saves model checkpoint to models/weights/ppo_scheduler.zip
"""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rl.oatrack_env import MaritimeSurveillanceEnv


def load_real_trajectories(results_dir="data/test_mp4"):
    """Extract real surveillance sequences from processed test video results."""
    results_dir = Path(results_dir)
    trajectories = []

    for json_file in results_dir.glob("*_result.json"):
        safe_name = json_file.stem.encode("ascii", "replace").decode("ascii")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            frames = data.get("frames", [])
            if not frames:
                continue

            traj = []
            for fr in frames:
                dets = fr.get("detections", [])
                tracks = fr.get("tracks", [])
                conf_list = [float(d.get("confidence", 0.0)) for d in dets]
                avg_conf = float(np.mean(conf_list)) if conf_list else 0.0

                # Compute motion proxy
                motion = 0.0
                if tracks:
                    motion = float(np.mean([abs(t.get("w", 0) - t.get("h", 0)) * 0.1 for t in tracks]))

                traj.append({
                    "ship_activity": 1.0 if len(dets) > 0 else 0.0,
                    "detections": len(dets),
                    "active_tracks": len(tracks),
                    "confidence": avg_conf,
                    "motion": motion,
                })

            if traj:
                trajectories.append(traj)
                print(f"Loaded real trajectory from {safe_name} ({len(traj)} steps)")
        except Exception as exc:
            print(f"Failed loading trajectory from {safe_name}: {exc}")

    # Add an empty sea trajectory (pure open ocean transit with zero detections)
    empty_traj = [{
        "ship_activity": 0.0,
        "detections": 0,
        "active_tracks": 0,
        "confidence": 0.0,
        "motion": 0.0,
    } for _ in range(300)]
    trajectories.append(empty_traj)
    print("Added synthetic empty sea transit trajectory (300 steps)")

    return trajectories


def train_ppo(
    total_timesteps=30000,
    seed=42,
    output_path="models/weights/ppo_scheduler.zip",
):
    print("=" * 65)
    print("TRAINING PPO ADAPTIVE COMPUTE SCHEDULER")
    print(f"Timesteps: {total_timesteps} | Seed: {seed} | Output: {output_path}")
    print("=" * 65)

    # Set seeds for reproducibility
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    trajectories = load_real_trajectories()

    # Create vectorized or single environment
    env = MaritimeSurveillanceEnv(trajectories=trajectories, max_steps=250)

    policy_kwargs = dict(
        net_arch=dict(pi=[64, 64], vf=[64, 64]),
        activation_fn=torch.nn.Tanh,
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=64,
        n_epochs=10,
        gamma=0.98,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs=policy_kwargs,
        seed=seed,
        verbose=1,
    )

    print("\nStarting PPO optimization...")
    model.learn(total_timesteps=total_timesteps)

    # Save trained policy
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_file.with_suffix("")))
    print(f"\n[OK] Trained PPO policy saved to: {output_path}")

    # Test policy quickly
    obs, _ = env.reset(seed=seed)
    actions_taken = []
    for _ in range(50):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        actions_taken.append(int(action))
        if terminated or truncated:
            break

    counts = {0: actions_taken.count(0), 1: actions_taken.count(1), 2: actions_taken.count(2)}
    print(f"Sample test rollout action distribution (50 steps): {counts}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=30000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="models/weights/ppo_scheduler.zip")
    args = parser.parse_args()

    train_ppo(
        total_timesteps=args.timesteps,
        seed=args.seed,
        output_path=args.output,
    )
