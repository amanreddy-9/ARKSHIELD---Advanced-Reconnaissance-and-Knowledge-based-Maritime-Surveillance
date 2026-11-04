"""
rl/scheduler.py
Adaptive Compute Scheduler with Real PPO Policy Integration & Safety Override.
Controls dynamic inference frequencies:
  - LOW:    every 4th frame (lightweight compute)
  - NORMAL: every 2nd frame (standard compute)
  - HIGH:   every 1st frame (full tactical compute)
"""
from pathlib import Path
import numpy as np

try:
    from stable_baselines3 import PPO
except Exception:
    PPO = None

from rl.oatrack_env import MaritimeSurveillanceEnv


class AdaptiveComputeScheduler:
    """
    Adaptive Edge-Compute Maritime Scheduler.
    Integrates trained Stable-Baselines3 PPO policy with an operational
    safety override layer and legacy rule-based fallback.
    """

    def __init__(self, model_path="models/weights/ppo_scheduler.zip", use_ppo=True):
        self.model_path = Path(model_path)
        self.use_ppo = use_ppo
        self.ppo_model = None
        self.ppo_ready = False
        self.recent_detections = []
        self.last_action = 1
        self.last_safety_override = False

        if self.use_ppo and PPO is not None:
            self.load_policy(self.model_path)

    def load_policy(self, model_path):
        """Load trained PPO policy weights."""
        model_p = Path(model_path)
        zip_path = model_p if model_p.suffix == ".zip" else model_p.with_suffix(".zip")
        if zip_path.exists():
            try:
                self.ppo_model = PPO.load(str(zip_path.with_suffix("")), device="cpu")
                self.ppo_ready = True
                print(f"[OK] AdaptiveComputeScheduler: Loaded PPO policy from {zip_path}")
            except Exception as e:
                print(f"[WARN] Failed to load PPO policy: {e}")
                self.ppo_ready = False
        else:
            self.ppo_ready = False

    def reset(self):
        """Reset scheduler internal buffers and state between video missions."""
        self.recent_detections.clear()
        self.last_action = 1
        self.last_safety_override = False

    def build_observation(
        self,
        target_visible,
        detection_count=0,
        active_track_count=0,
        avg_confidence=0.0,
        motion_level=0.0,
        frame_progress=0.5,
    ):
        """Build normalized 8-dimensional state vector for PPO."""
        self.recent_detections.append(detection_count)
        if len(self.recent_detections) > 10:
            self.recent_detections.pop(0)
        recent_avg = float(np.mean(self.recent_detections))

        return np.array([
            1.0 if target_visible else 0.0,
            min(detection_count / 10.0, 1.0),
            min(recent_avg / 10.0, 1.0),
            min(active_track_count / 10.0, 1.0),
            min(motion_level / 30.0, 1.0),
            min(max(avg_confidence, 0.0), 1.0),
            float(self.last_action / 2.0),
            float(min(max(frame_progress, 0.0), 1.0)),
        ], dtype=np.float32)

    def select_action(self, obs):
        """
        Query PPO policy, then apply Safety Override Layer.
        Returns:
            (effective_action, mode_string, safety_override_triggered)
        """
        raw_action = 1

        if self.ppo_ready and self.ppo_model is not None:
            try:
                pred, _ = self.ppo_model.predict(obs, deterministic=True)
                raw_action = int(pred)
            except Exception:
                raw_action = 1
        else:
            # Rule-based fallback if PPO weights not loaded
            ship_present = obs[0] > 0.5
            det_cnt = obs[1] * 10.0
            if not ship_present and det_cnt == 0:
                raw_action = 0  # LOW
            elif det_cnt >= 3 or obs[3] >= 0.2:
                raw_action = 2  # HIGH
            else:
                raw_action = 1  # NORMAL

        # Apply Safety Override Layer
        effective_action, safety_override = MaritimeSurveillanceEnv.check_safety_override(
            raw_action, obs
        )

        self.last_action = effective_action
        self.last_safety_override = safety_override
        mode_str = MaritimeSurveillanceEnv.MODE_MAPPING[effective_action]

        return effective_action, mode_str, safety_override

    def select_mode(self, target_visible, scene_complexity=0.0, obs=None):
        """
        Backwards-compatible API for pipeline orchestrator.
        """
        if obs is None:
            obs = self.build_observation(
                target_visible=target_visible,
                detection_count=1 if target_visible else 0,
                active_track_count=1 if target_visible else 0,
                avg_confidence=0.85 if target_visible else 0.0,
            )

        action, mode, override = self.select_action(obs)
        return mode
