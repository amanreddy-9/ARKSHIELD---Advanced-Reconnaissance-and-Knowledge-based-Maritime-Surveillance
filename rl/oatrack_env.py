"""
rl/oatrack_env.py
Gymnasium Environment for PPO-Based Adaptive Maritime Surveillance
Dynamically throttles compute resources (LOW / NORMAL / HIGH) based on
vessel presence, tracking continuity, scene complexity, and edge energy budget.
"""
import gymnasium as gym
from gymnasium import spaces
import numpy as np


class MaritimeSurveillanceEnv(gym.Env):
    """
    Adaptive Edge-Compute Maritime Surveillance Gymnasium Environment.

    Actions:
        0: LOW     -> Process every 4th frame (Compute cost ~0.25)
        1: NORMAL  -> Process every 2nd frame (Compute cost ~0.50)
        2: HIGH    -> Process every 1st frame (Compute cost ~1.00)

    Observations (Box[8], normalized in [0.0, 1.0]):
        0: ship_activity         (1.0 if vessel present, 0.0 otherwise)
        1: current_detections    (count / 10.0, clipped to 1.0)
        2: recent_detection_avg  (moving average over 10 frames / 10.0)
        3: active_tracks         (active track count / 10.0)
        4: motion_level          (normalized pixel velocity / 30.0)
        5: avg_confidence        (average detection confidence in [0, 1])
        6: previous_action       (action / 2.0 in [0.0, 1.0])
        7: frame_progress        (current_step / max_steps in [0.0, 1.0])
    """

    metadata = {"render_modes": ["human"]}

    ACTION_LOW = 0
    ACTION_NORMAL = 1
    ACTION_HIGH = 2

    ACTION_NAMES = {0: "LOW", 1: "NORMAL", 2: "HIGH"}
    MODE_MAPPING = {0: "lightweight", 1: "standard", 2: "heavy"}
    COMPUTE_COSTS = {0: 0.25, 1: 0.50, 2: 1.00}

    def __init__(self, trajectories=None, max_steps=200):
        super().__init__()
        self.max_steps = max_steps
        self.trajectories = trajectories or []

        # Action space: Discrete(3) -> LOW, NORMAL, HIGH
        self.action_space = spaces.Discrete(3)

        # Observation space: 8 normalized features
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(8,),
            dtype=np.float32,
        )

        self.current_step = 0
        self.current_trajectory = None
        self.prev_action = 1
        self.recent_detections = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.prev_action = 1
        self.recent_detections = []

        if self.trajectories:
            # Pick a trajectory from cached video runs
            traj_idx = self.np_random.integers(0, len(self.trajectories))
            self.current_trajectory = self.trajectories[traj_idx]
        else:
            self.current_trajectory = None

        obs = self._get_obs()
        return obs, {}

    def _get_obs(self):
        if self.current_trajectory and self.current_step < len(self.current_trajectory):
            step_data = self.current_trajectory[self.current_step]
            ship_act = float(step_data.get("ship_activity", 0.0))
            det_cnt = float(step_data.get("detections", 0.0))
            active_tr = float(step_data.get("active_tracks", 0.0))
            motion = float(step_data.get("motion", 0.0))
            conf = float(step_data.get("confidence", 0.0))
        else:
            # Synthetic trajectory generator for training diversity
            # Simulates encounters: empty transit -> target approach -> escort -> departure
            progress = self.current_step / max(1, self.max_steps)
            if 0.25 <= progress <= 0.75:
                # Active target encounter
                ship_act = 1.0
                det_cnt = float(self.np_random.integers(1, 4))
                active_tr = float(self.np_random.integers(1, 3))
                motion = float(self.np_random.uniform(2.0, 15.0))
                conf = float(self.np_random.uniform(0.70, 0.98))
            else:
                # Empty sea transit
                ship_act = 0.0
                det_cnt = 0.0
                active_tr = 0.0
                motion = 0.0
                conf = 0.0

        self.recent_detections.append(det_cnt)
        if len(self.recent_detections) > 10:
            self.recent_detections.pop(0)
        recent_avg = float(np.mean(self.recent_detections))

        obs = np.array([
            min(1.0, max(0.0, ship_act)),
            min(1.0, max(0.0, det_cnt / 10.0)),
            min(1.0, max(0.0, recent_avg / 10.0)),
            min(1.0, max(0.0, active_tr / 10.0)),
            min(1.0, max(0.0, motion / 30.0)),
            min(1.0, max(0.0, conf)),
            float(self.prev_action / 2.0),
            float(self.current_step / max(1, self.max_steps)),
        ], dtype=np.float32)

        return obs

    def step(self, action):
        action = int(action)
        obs = self._get_obs()

        ship_present = obs[0] > 0.5
        active_tracks = obs[3] > 0.05
        compute_cost = self.COMPUTE_COSTS[action]

        # Reward balancing detection quality + continuity vs compute penalty
        compute_penalty = 0.35 * compute_cost

        if ship_present or active_tracks:
            # Active vessel scene: reward maintaining awareness and continuity
            if action == self.ACTION_HIGH:
                awareness_reward = 1.20
            elif action == self.ACTION_NORMAL:
                awareness_reward = 0.75
            else:  # LOW during active vessel encounter is strongly penalized!
                awareness_reward = -1.50
            reward = awareness_reward - compute_penalty
        else:
            # Empty water / transit scene: reward compute savings (LOW), penalize waste
            if action == self.ACTION_LOW:
                economy_reward = 0.90
            elif action == self.ACTION_NORMAL:
                economy_reward = 0.30
            else:  # HIGH on empty open water is penalized as compute waste
                economy_reward = -0.70
            reward = economy_reward - compute_penalty

        self.prev_action = action
        self.current_step += 1

        terminated = self.current_step >= self.max_steps
        truncated = False

        next_obs = self._get_obs()
        info = {
            "action": action,
            "action_name": self.ACTION_NAMES[action],
            "mode": self.MODE_MAPPING[action],
            "compute_cost": compute_cost,
            "ship_present": ship_present,
            "active_tracks": active_tracks,
        }

        return next_obs, float(reward), terminated, truncated, info

    @staticmethod
    def check_safety_override(raw_action, obs):
        """
        Operational Safety Override Layer.
        Prevents PPO from selecting an unsafe LOW processing mode during
        sudden target appearance, multiple active tracks, or high detection confidence.

        Returns:
            (effective_action, safety_override_triggered)
        """
        ship_activity = float(obs[0])
        current_dets = float(obs[1])
        active_tracks = float(obs[3])
        avg_confidence = float(obs[5])

        # Rule 1: Sudden vessel appearance or high confidence detection
        if (ship_activity > 0.5 or current_dets > 0.05 or avg_confidence >= 0.70) and raw_action == 0:
            return 1, True  # Override LOW to at least NORMAL

        # Rule 2: Multiple confirmed tracks in scene
        if active_tracks >= 0.20 and raw_action < 2:
            return 2, True  # Override to HIGH for multi-target tracking

        return raw_action, False
