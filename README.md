# ARKSHIELD
### Advanced Reconnaissance and Knowledge-based Maritime Surveillance System

**A Hierarchical Multimodal Framework for Autonomous Maritime Surveillance and Intelligence Generation**

ARKSHIELD is an AI-powered maritime surveillance and threat intelligence platform that integrates high-resolution satellite vessel detection, tactical UAV surveillance, persistent multi-object tracking, fine-grained vessel classification, adaptive edge-compute optimization, and grounded vision-language reasoning into a unified surveillance framework.

The system bridges strategic wide-area satellite reconnaissance with localized aerial inspection, enabling automated vessel identification, continuous tracking, and telemetry-grounded intelligence generation through an integrated Maritime Surveillance Command Center.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Key Capabilities](#key-capabilities)
- [Technical Methodology](#technical-methodology)
- [Technology Stack](#technology-stack)
- [Datasets](#datasets)
- [Experimental Results](#experimental-results)
- [System Workflow](#system-workflow)
- [Application Interface](#application-interface)
- [API Architecture](#api-architecture)
- [Development Environment](#development-environment)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)

---

## Overview

Modern maritime surveillance requires continuous monitoring across vast oceanic regions while maintaining the ability to inspect individual vessels at a tactical level. Conventional surveillance architectures often operate satellite reconnaissance and UAV monitoring as disconnected systems, resulting in delayed target identification, inefficient aerial searches, and fragmented tracking.

ARKSHIELD addresses these challenges through a hierarchical multimodal architecture consisting of three primary operational tiers:

1. **Strategic Surveillance:** High-resolution satellite imagery analysis and automated vessel localization using YOLO11n.
2. **Tactical Surveillance:** UAV video analysis, persistent multi-object tracking, and reinforcement-learning-based adaptive compute scheduling.
3. **Intelligence Generation:** Fine-grained vessel classification and grounded vision-language reasoning for automated maritime intelligence briefings.

The framework combines computer vision, temporal tracking, deep reinforcement learning, and multimodal language models to establish an integrated perception-to-intelligence pipeline.

---

## System Architecture

ARKSHIELD operates through three interconnected surveillance tiers.

### 1. Strategic Satellite Surveillance

- Processes high-resolution optical satellite imagery.
- Uses a fine-tuned YOLO11n detector at 1024 × 1024 input resolution.
- Identifies vessels and extracts bounding-box coordinates, centroids, dimensions, and confidence scores.
- Packages detected target coordinates through an automated handoff adapter.
- Generates localized UAV inspection cues to eliminate blind open-ocean searching.

### 2. Tactical UAV Surveillance

- Ingests sequential UAV video feeds in MP4/AVI formats.
- Implements persistent multi-object tracking to maintain vessel identities across video frames.
- Uses motion estimation and multi-feature data association to handle temporary detection dropouts.
- Applies geometric containment suppression to eliminate internal vessel component false alarms.
- Integrates a PPO-based scheduler to dynamically regulate visual inference frequency.

### 3. Multimodal Intelligence Generation

- Classifies confirmed vessel tracks into ten maritime categories using ConvNeXt-Tiny.
- Aggregates classification probabilities across multiple frames to improve prediction stability.
- Integrates Groq-hosted vision-language models for contextual intelligence generation.
- Produces structured, telemetry-grounded surveillance briefings.
- Displays vessel information, tracking data, and intelligence outputs through the React-based command center.

---

## Key Capabilities

| Capability | Implementation |
|---|---|
| Satellite Vessel Detection | YOLO11n |
| Target Localization | Automated Coordinate Handoff |
| UAV Multi-Object Tracking | Motion Estimation and Data Association |
| Tracking Persistence | Kalman Filtering and Hungarian Matching |
| False Alarm Suppression | Geometric Containment Filtering |
| Vessel Classification | ConvNeXt-Tiny |
| Temporal Classification | Multi-Frame Evidence Aggregation |
| Adaptive Compute Optimization | PPO Reinforcement Learning |
| Intelligence Generation | Vision-Language Models |
| Operational Dashboard | React |
| Backend Services | FastAPI |

---

## Technical Methodology

### 1. High-Resolution Vessel Detection

A fine-tuned YOLO11n model processes optical satellite imagery at 1024 × 1024 resolution using the VHRV benchmark.

The detector generates:
- Vessel bounding boxes.
- Detection confidence scores.
- Centroid coordinates.
- Bounding-box width and height.
- Total vessel count.

High-resolution processing preserves spatial information associated with smaller vessels that may otherwise be lost through aggressive image downsampling.

### 2. Satellite-to-UAV Target Handoff

The target handoff adapter converts satellite detection outputs into structured surveillance cues.

Detected vessel coordinates and bounding geometries are transformed into simulated geographic waypoints to initialize localized UAV inspection sectors.

The current implementation uses a software-in-the-loop simulation rather than direct physical flight-controller integration.

### 3. Persistent UAV Tracking

The tactical surveillance module maintains vessel identities across sequential UAV video frames, even under challenging maritime conditions such as temporary occlusion, sea spray, camera movement, and detection dropouts.

The tracking pipeline incorporates:

- Motion prediction and state estimation.
- Multi-feature data association.
- Hungarian matching for detection-to-track assignment.
- Bounding-box geometric containment suppression.
- Track persistence across temporary detection failures.

An 8-state discrete linear Kalman Filter is used internally to estimate vessel position, bounding-box dimensions, and their corresponding rates of change.

The tracking association mechanism considers:
- Intersection over Union (IoU).
- Normalized centroid displacement.
- Bounding-box size similarity.
- Motion-heading similarity.

This combination helps reduce identity fragmentation and suppress false detections originating from internal vessel components.

### 4. Fine-Grained Vessel Classification

Confirmed vessel tracks are classified using ConvNeXt-Tiny trained on the TITANIC-FGS-10 dataset.

The system recognizes ten categories:

1. Aircraft Carrier
2. Amphibious Assault Ship
3. Cruise Ship
4. Cruiser
5. Destroyer
6. Frigate
7. Littoral Combat Ship
8. Non-Ship Clutter
9. Oil Tanker
10. Yacht

Multi-frame temporal evidence aggregation combines classification probabilities across a vessel's tracking lifetime to produce more stable track-level predictions.

### 5. PPO-Based Adaptive Edge Computing

ARKSHIELD integrates a Proximal Policy Optimization (PPO) agent trained using Gymnasium and Stable-Baselines3.

The scheduler dynamically selects between three inference modes:

- **LOW:** Reduced inference frequency (every fourth frame).
- **NORMAL:** Standard inference frequency.
- **HIGH:** Full-rate inference.

The policy considers scene visibility, detection activity, tracking continuity, motion, confidence, and mission progress.

A deterministic safety override prevents excessive inference reduction when targets are detected and enforces HIGH mode during multi-target encounters.

### 6. Grounded Vision-Language Reasoning

The intelligence generation layer integrates Groq-hosted vision-language models, including:

- Qwen-2.5-Vision-72B
- Llama-3.3-70B

Verified telemetry, vessel counts, persistent Track IDs, bounding-box coordinates, classification probabilities, and relevant visual crops are supplied through structured prompts.

The reasoning layer generates natural-language intelligence briefings while restricting unsupported claims about unobservable attributes such as vessel nationality, registration numbers, and weapon systems.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.10 |
| Deep Learning | PyTorch |
| Object Detection | Ultralytics YOLO11n |
| Image Classification | ConvNeXt-Tiny, timm |
| Computer Vision | OpenCV, Pillow |
| Numerical Computing | NumPy, SciPy |
| Multi-Object Tracking | Kalman Filter, Hungarian Algorithm |
| Reinforcement Learning | Gymnasium, Stable-Baselines3, PPO |
| Vision-Language Models | Qwen-2.5-Vision, Llama-3.3-70B |
| AI Inference API | Groq Cloud API |
| Backend | FastAPI, Uvicorn, Starlette |
| Frontend | React, Vite |
| Data Exchange | REST APIs, JSON |

---

## Datasets

ARKSHIELD utilizes two benchmark datasets for its satellite detection and fine-grained vessel classification components.

### 1. VHRV – Very-High-Resolution Vessel Dataset

Used for strategic satellite-based vessel detection.

| Split | Images | Vessel Instances |
|---|---:|---:|
| Training | 1,052 | 7,125 |
| Validation | 300 | 1,842 |
| Testing | 150 | 1,191 |
| **Total** | **1,502** | **10,158** |

- High-resolution optical satellite imagery.
- Authentic horizontal bounding-box annotations.
- Covers open waters, coastlines, anchorages, and dense harbors.

### 2. TITANIC-FGS-10 – Fine-Grained Ship Classification Dataset

Used for tactical vessel classification.

| Split | Images |
|---|---:|
| Training | 12,000 |
| Validation | 1,285 |
| Testing | 1,285 |
| **Total** | **14,570** |

Contains ten maritime categories covering naval combatants, commercial vessels, civilian vessels, and non-ship clutter.

---

## Experimental Results

The following results were obtained through the experiments documented in the project report.

### Satellite Vessel Detection

YOLO11n evaluated on the independent VHRV test split:

| Metric | Result |
|---|---:|
| Precision | 93.64% |
| Recall | 90.26% |
| mAP@50 | 94.63% |
| mAP@50-95 | 74.16% |
| Mean Bounding Box IoU | 0.863 |
| Inference Latency | 17.75 ms |
| Throughput | 56.35 FPS |

### UAV Tracking Performance

| Metric | Result |
|---|---:|
| Track Fragmentation | Reduced from 27 IDs to 2 |
| Internal Deck False Alarm Suppression | 100% |
| Representative Track Stability | 100% |

### Vessel Classification

ConvNeXt-Tiny evaluated on the TITANIC-FGS-10 test split:

| Metric | Result |
|---|---:|
| Top-1 Accuracy | 81.56% |
| Precision | 82.84% |
| Recall | 83.22% |
| Macro F1-Score | 82.84% |

### PPO Adaptive Compute Optimization

| Surveillance Scenario | Estimated Compute Reduction |
|---|---:|
| Empty Sea Transit | 75.00% |
| Oil Tanker Mission | 45.46% |
| Cruise Ship Mission | 52.12% |
| Destroyer Naval Patrol | 16.98% |
| Frigate Surveillance | 27.76% |

*Note: Compute reductions represent estimated algorithmic processing and forward-pass savings, not directly measured physical battery consumption.*

---

## System Workflow

The complete surveillance pipeline follows this sequence:

```text
       SATELLITE IMAGE INPUT
                |
                v
       YOLO11n VESSEL DETECTION
                |
                v
       TARGET COORDINATE HANDOFF
                |
                v
         UAV VIDEO INGESTION
                |
                v
       PPO ADAPTIVE SCHEDULER
                |
                v
        PERSISTENT UAV TRACKING
                |
                v
       CONVNEXT-TINY CLASSIFICATION
                |
                v
       TEMPORAL EVIDENCE AGGREGATION
                |
                v
       GROQ VISION-LANGUAGE REASONING
                |
                v
       MARITIME INTELLIGENCE BRIEFING
                |
                v
       REACT SURVEILLANCE COMMAND CENTER
```

---

## Application Interface

The React-based Maritime Surveillance Command Center provides an interactive operational interface comprising:

**1. Satellite Scan Console**
- Satellite image upload.
- Vessel detection overlays.
- Automated vessel count.
- Intelligence briefing generation.

**2. Tactical Drone Video Console**
- UAV video playback.
- Vessel bounding boxes.
- Persistent tracking IDs.
- Movement trajectories and tracking stability.

**3. PPO Compute Analytics Panel**
- Adaptive inference modes.
- PPO action distribution.
- Estimated compute savings.

**4. Diagnostic Gallery**
- Multi-vessel evaluation.
- Vessel crop inspection.
- Detection and classification diagnostics.

---

## API Architecture

The backend is implemented using FastAPI and exposes RESTful services.

| Endpoint | Function |
|---|---|
| `/satellite/detect` | Satellite image vessel detection |
| `/drone/video` | Tactical UAV video processing |
| `/health` | Backend health monitoring |

JSON-based telemetry is used to exchange detection, tracking, classification, and intelligence information between system components.

---

## Development Environment

The project was developed and benchmarked using the following configuration:

| Component | Specification |
|---|---|
| Operating System | Windows 11 (64-bit) |
| Python | 3.10.11 |
| PyTorch | 2.14.0 + CUDA 12.6 |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| GPU Memory | 4 GB |
| YOLO11 | Ultralytics 8.3+ |
| FastAPI | 0.115.0 |
| Uvicorn | 0.30.0 |
| OpenCV | 4.10.0 |
| Gymnasium | 0.29.1 |
| Stable-Baselines3 | 2.3.2 |

---

## Limitations

The current research prototype has the following operational boundaries:

- **Horizontal Bounding Boxes:** The current satellite detection baseline uses HBB annotations. Oriented Bounding Box detection is not included.
- **Software-in-the-Loop UAV Integration:** Physical UAV flight-controller integration through PX4/ArduPilot and MAVLink has not been implemented.
- **Estimated Compute Savings:** Reported compute reductions are algorithmic estimates rather than direct hardware power measurements.
- **Vessel Classification Ambiguity:** Visually similar naval combatants, particularly Destroyers, Frigates, and Cruisers, remain challenging to distinguish from individual frames.
- **Vision-Language Grounding:** Intelligence generation is restricted to available sensor telemetry and visual evidence.

---

## Future Enhancements

Planned research and engineering extensions include:

- Integration of Oriented Bounding Box (OBB) detection using YOLO11-OBB.
- Hardware-in-the-loop UAV autopilot integration using PX4/ArduPilot and MAVLink.
- Embedded inference optimization using NVIDIA TensorRT and INT8 quantization.
- Deployment on NVIDIA Jetson Orin Nano platforms.
- Multimodal Synthetic Aperture Radar (SAR) and thermal imagery fusion.
- Lightweight on-device vision-language models for reduced cloud API dependency.

---

## Project Scope

ARKSHIELD is developed as an integrated research and software prototype for hierarchical maritime surveillance, combining strategic satellite reconnaissance, tactical UAV tracking, adaptive computing, fine-grained vessel recognition, and grounded multimodal intelligence generation.

The project demonstrates how multiple AI and computational techniques can work together to establish a unified maritime perception-to-intelligence pipeline.

**ARKSHIELD — Autonomous Awareness. Persistent Surveillance. Intelligent Maritime Defence.**
