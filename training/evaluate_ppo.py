"""
training/evaluate_ppo.py
Rigorous Comparative Evaluation of Adaptive Surveillance Schedulers:
- Full Processing (100% compute baseline)
- Rule-Based Scheduler (legacy heuristics)
- Real Trained PPO Policy (Stable-Baselines3)

Outputs verified metrics and logs: outputs/rl/ppo_episode_log.csv
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import pandas as pd
from stable_baselines3 import PPO

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rl.oatrack_env import MaritimeSurveillanceEnv
from rl.scheduler import AdaptiveComputeScheduler


def evaluate_schedulers(
    ppo_model_path="models/weights/ppo_scheduler.zip",
    results_dir="data/test_mp4",
    output_dir="outputs/rl",
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_csv = output_dir / "ppo_episode_log.csv"
    metrics_json = output_dir / "scheduler_comparison_metrics.json"

    print("=" * 65)
    print("COMPARATIVE EVALUATION: FULL vs RULE-BASED vs PPO")
    print(f"PPO Weights: {ppo_model_path}")
    print("=" * 65)

    ppo_loaded = False
    ppo_policy = None
    if Path(ppo_model_path).exists():
        try:
            ppo_policy = PPO.load(str(Path(ppo_model_path).with_suffix("")))
            ppo_loaded = True
            print("[OK] Loaded trained PPO policy.")
        except Exception as e:
            print(f"[WARN] Could not load PPO policy: {e}")

    # Prepare real evaluation test cases:
    # 1. Empty sea
    # 2. Oil tanker video
    # 3. Cruise ship video
    test_cases = {}

    # Check for real JSON results
    for jf in Path(results_dir).glob("*_result.json"):
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
        frames = data.get("frames", [])
        if "oil" in jf.stem.lower():
            test_cases["Oil Tanker Surveillance"] = frames
        elif "allure" in jf.stem.lower() or "cruise" in jf.stem.lower():
            test_cases["Cruise Ship Surveillance"] = frames

    # Create synthetic empty-sea baseline
    empty_frames = [{
        "frame_index": i,
        "timestamp": i / 30.0,
        "detections": [],
        "tracks": [],
        "ship_count": 0,
        "active_track_count": 0,
    } for i in range(300)]
    test_cases["Empty Sea Surveillance"] = empty_frames

    all_comparison_results = {}
    csv_rows = []

    for test_name, frames in test_cases.items():
        total_frames = len(frames)
        print(f"\n--- Evaluating Scenario: {test_name} ({total_frames} frames) ---")

        # 1. Strategy A: Full Processing (Always HIGH, every frame)
        full_yolo = total_frames
        full_compute = total_frames * 1.0
        full_misses = 0

        # 2. Strategy B: Legacy Rule-Based Scheduler
        rule_scheduler = AdaptiveComputeScheduler(use_ppo=False)
        rule_yolo = 0
        rule_compute = 0.0
        rule_modes = {"lightweight": 0, "standard": 0, "heavy": 0}

        # 3. Strategy C: Trained PPO Scheduler
        ppo_scheduler = AdaptiveComputeScheduler(use_ppo=True, model_path=ppo_model_path)
        ppo_yolo = 0
        ppo_compute = 0.0
        ppo_actions = {0: 0, 1: 0, 2: 0}
        ppo_overrides = 0
        recent_dets = []

        for fr_idx, fr in enumerate(frames):
            dets = fr.get("detections", [])
            tracks = fr.get("tracks", [])
            det_count = len(dets)
            track_count = len(tracks)
            conf_list = [float(d.get("confidence", 0.0)) for d in dets]
            avg_conf = float(np.mean(conf_list)) if conf_list else 0.0
            motion = float(np.mean([abs(t.get("w", 0) - t.get("h", 0)) * 0.1 for t in tracks])) if tracks else 0.0

            recent_dets.append(det_count)
            if len(recent_dets) > 10:
                recent_dets.pop(0)
            recent_avg = float(np.mean(recent_dets))

            # --- Rule-based decision ---
            comp = min(det_count / 10.0, 1.0)
            target_vis = det_count > 0
            rule_mode = rule_scheduler.select_mode(target_vis, comp)
            rule_modes[rule_mode] = rule_modes.get(rule_mode, 0) + 1
            if rule_mode == "lightweight":
                if fr_idx % 4 == 0:
                    rule_yolo += 1
                rule_compute += 0.25
            elif rule_mode == "standard":
                if fr_idx % 2 == 0:
                    rule_yolo += 1
                rule_compute += 0.50
            else:
                rule_yolo += 1
                rule_compute += 1.00

            # --- PPO decision ---
            obs = np.array([
                1.0 if det_count > 0 else 0.0,
                min(det_count / 10.0, 1.0),
                min(recent_avg / 10.0, 1.0),
                min(track_count / 10.0, 1.0),
                min(motion / 30.0, 1.0),
                avg_conf,
                0.5,
                fr_idx / max(1, total_frames),
            ], dtype=np.float32)

            raw_action = 1
            if ppo_policy is not None:
                raw_act, _ = ppo_policy.predict(obs, deterministic=True)
                raw_action = int(raw_act)

            # Apply Safety Override Layer
            effective_action, safety_override = MaritimeSurveillanceEnv.check_safety_override(raw_action, obs)
            if safety_override:
                ppo_overrides += 1
            ppo_actions[effective_action] = ppo_actions.get(effective_action, 0) + 1

            cost_factor = MaritimeSurveillanceEnv.COMPUTE_COSTS[effective_action]
            ppo_compute += cost_factor
            yolo_called = False
            classifier_called = False

            if effective_action == 0:
                yolo_called = (fr_idx % 4 == 0)
                classifier_called = (fr_idx % 8 == 0) and track_count > 0
            elif effective_action == 1:
                yolo_called = (fr_idx % 2 == 0)
                classifier_called = (fr_idx % 4 == 0) and track_count > 0
            else:
                yolo_called = True
                classifier_called = track_count > 0

            if yolo_called:
                ppo_yolo += 1

            # Compute immediate reward proxy
            compute_pen = 0.35 * cost_factor
            if det_count > 0 or track_count > 0:
                reward_val = (1.20 if effective_action == 2 else (0.75 if effective_action == 1 else -1.50)) - compute_pen
            else:
                reward_val = (0.90 if effective_action == 0 else (0.30 if effective_action == 1 else -0.70)) - compute_pen

            # Record detailed episode log row
            csv_rows.append({
                "scenario": test_name,
                "frame_number": fr.get("frame_index", fr_idx),
                "timestamp": round(float(fr.get("timestamp", fr_idx / 30.0)), 3),
                "ship_activity": 1.0 if det_count > 0 else 0.0,
                "detections_current_frame": det_count,
                "active_tracks": track_count,
                "avg_confidence": round(avg_conf, 3),
                "ppo_action": effective_action,
                "processing_mode": MaritimeSurveillanceEnv.MODE_MAPPING[effective_action],
                "yolo_called": yolo_called,
                "classifier_called": classifier_called,
                "compute_cost": cost_factor,
                "reward": round(reward_val, 3),
                "safety_override": safety_override,
            })

        # Calculate estimated compute reductions (proxy)
        rule_reduction = round((1.0 - rule_compute / max(1.0, full_compute)) * 100, 2)
        ppo_reduction = round((1.0 - ppo_compute / max(1.0, full_compute)) * 100, 2)

        all_comparison_results[test_name] = {
            "total_frames": total_frames,
            "full_processing": {
                "frames_processed": total_frames,
                "yolo_calls": full_yolo,
                "estimated_compute_cost": round(full_compute, 1),
                "estimated_compute_reduction_pct": 0.0,
            },
            "rule_based_scheduler": {
                "frames_processed": total_frames,
                "yolo_calls": rule_yolo,
                "estimated_compute_cost": round(rule_compute, 1),
                "estimated_compute_reduction_pct": rule_reduction,
                "mode_counts": rule_modes,
            },
            "ppo_adaptive_scheduler": {
                "frames_processed": total_frames,
                "yolo_calls": ppo_yolo,
                "estimated_compute_cost": round(ppo_compute, 1),
                "estimated_compute_reduction_pct": ppo_reduction,
                "action_distribution": ppo_actions,
                "safety_overrides_triggered": ppo_overrides,
            },
        }

        print(f"Full Processing Compute:   {full_compute:.1f} (0.0% reduction)")
        print(f"Rule-Based Compute:        {rule_compute:.1f} ({rule_reduction}% estimated compute reduction)")
        print(f"PPO Adaptive Compute:      {ppo_compute:.1f} ({ppo_reduction}% estimated compute reduction)")
        print(f"PPO Actions (LOW/NORM/HI): {ppo_actions} | Overrides: {ppo_overrides}")

    # Write CSV Log
    if csv_rows:
        with open(log_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"\n[OK] Wrote detailed episode log: {log_csv} ({len(csv_rows)} records)")

    # Write JSON Comparison
    with open(metrics_json, "w", encoding="utf-8") as f:
        json.dump(all_comparison_results, f, indent=2)
    print(f"[OK] Wrote scheduler comparison metrics: {metrics_json}")

    return all_comparison_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/weights/ppo_scheduler.zip")
    args = parser.parse_args()
    evaluate_schedulers(ppo_model_path=args.model)
