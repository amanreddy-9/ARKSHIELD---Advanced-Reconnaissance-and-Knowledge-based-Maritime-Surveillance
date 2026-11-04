# OATrack-VLM: Complete System Replication, Deployment & Wiring Guide

This document provides a comprehensive operational breakdown of **OATrack-VLM** (*Occlusion-Aware Tracking and Vision-Language Reasoning for Adaptive Maritime Surveillance*). It covers the live architecture, frontend-backend connection topology, current running status, exact training and testing datasets/models being used, and a complete step-by-step procedure to clone this repository onto a fresh system, download datasets separately, and wire the entire system to run successfully.

---

## 1. System Architecture & Component Overview

OATrack-VLM is an end-to-end multi-modal maritime surveillance platform operating across both satellite overhead imagery and tactical drone video feeds:

```
                                 +-------------------------------------------------+
                                 |         Modern React Frontend (Vite)            |
                                 |     Port: 5173  |  shadcn/ui + TanStack Router  |
                                 +------------------------+------------------------+
                                                          | HTTP REST / JSON
                                                          v
                                 +-------------------------------------------------+
                                 |             FastAPI Backend Engine              |
                                 |          Port: 8000  |  Uvicorn Worker          |
                                 +------------------------+------------------------+
                                                          |
             +-----------------------+--------------------+-----------------------+-----------------------+
             |                       |                                            |                       |
             v                       v                                            v                       v
+------------------------+  +-----------------------------------------------+  +-------------------+  +-------------------+
|  YOLO11n-VHRV Detector |  | Continuous Kalman Tracker (Hungarian Matching) |  | ConvNeXt-Tiny     |  | Groq VLM Guard    |
|  1024px HBB Detection  |  | 8-State Vector: [cx, cy, w, h, vx, vy, vw, vh]|  | 10-Class Vessel   |  | Qwen 2.5 Vision   |
|  vhrv_best.pt (5.4MB)  |  | Occlusion Recovery + Duplicate Birth Deferral |  | Fine-Grained      |  | Token Throttling  |
+------------------------+  +-----------------------------------------------+  | best.pt (106MB)   |  | In-Memory Caching |
             |                                                                 +-------------------+  +-------------------+
             +---------------------------------------+------------------------------------+
                                                     v
                                 +-------------------------------------------------+
                                 |  PPO Adaptive Compute Scheduler (Gymnasium RL)  |
                                 |   Dynamic Skip / Scan / Heavy Execution Modes   |
                                 |           ppo_scheduler.zip (148KB)             |
                                 +-------------------------------------------------+
```

### Core Subsystems:
1. **High-Resolution Satellite Vessel Detector**:
   - Model: Fine-tuned **YOLO11n-VHRV** trained at 1024x1024 resolution on the VHRV (Very High Resolution Vessel) optical dataset.
   - Outputs: Horizontal Bounding Boxes (HBB), detection confidence, and normalized spatial centroids.
   - Alternate Model: Custom anchor-free detector (`models/weights/vhrv_custom_best.pt`).
2. **Continuous Kalman Drone Tracker**:
   - Architecture: 8-state Kalman Filter (`cx, cy, w, h, vx, vy, vw, vh`) with stage-based Hungarian data association (IoU + Centroid proximity + Aspect similarity + Velocity continuity).
   - Occlusion & Coasting: Retains and projects tracks across missed detector frames (e.g. cloud, bridge, or smoke occlusions) up to an aging threshold before deletion.
   - Spatial Deferral: Defer duplicate track birth when proposals land within confirmed vessel footprints.
3. **Fine-Grained 10-Class Vessel Classifier**:
   - Model: **ConvNeXt-Tiny** fine-grained classifier fine-tuned on the TITANIC-FGS-10 dataset.
   - Classes (10): `Destroyer`, `Frigate`, `Aircraft_carrier`, `Amphibious_assault_ship`, `Cruiser`, `Littoral_combat_ship`, `Cruise_ship`, `Oil_tanker`, `Yacht`, `Non_ship`.
   - Temporal Smoothing: Maintains cumulative candidate distribution scores over multi-frame observations.
4. **Adaptive Edge Compute Scheduler (PPO RL)**:
   - Policy: Stable-Baselines3 Gymnasium PPO policy (`ppo_scheduler.zip`).
   - Dynamically selects execution modes (`skip`, `scan`, `heavy`) based on track velocity, target presence, and scene stability to cut redundant edge inference compute.
5. **Vision-Language Reasoning (Groq VLM)**:
   - Engine: Groq Vision API running `qwen/qwen3.8-27b` / LLaVA-based vision models.
   - Reliability Guard: Shared in-memory rate-limiter, token-bucket admission, automatic 429 backoff handling, and 1-hour cache layer to prevent quota exhaustion.

---

## 2. Frontend & Backend Connections

### Network Topology:
| Component | Technology | Default Host & Port | Configuration Location |
| :--- | :--- | :--- | :--- |
| **Backend API** | FastAPI / Uvicorn | `http://127.0.0.1:8000` | `backend/main.py` |
| **Frontend UI** | Vite / React 19 / TS | `http://localhost:5173` | `frontend/.env` (`VITE_API_BASE_URL`) |

### CORS & Security:
The FastAPI backend enables `CORSMiddleware` with `allow_origins=["*"]`, `allow_methods=["*"]`, and `allow_headers=["*"]`, ensuring seamless client interactions from `localhost:5173` or local network IPs.

### Static Asset Serving:
The backend mounts local folders directly to serve processed media to the frontend:
- `/static/outputs` -> `OATrack-VLM/outputs`
- `/static/data` -> `OATrack-VLM/data`

### REST API Endpoints:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Rapid liveness check (`{"status": "ok", "project": "OATrack-VLM"}`) |
| `GET` | `/system/health` | Comprehensive GPU/CUDA telemetry and detector/tracker/classifier status |
| `GET` | `/satellite/presets` | List pre-indexed high-res satellite evaluation images |
| `POST` | `/satellite/detect-preset` | Run YOLO11n detection + Groq VLM briefing on a preset image |
| `POST` | `/satellite/detect` | Upload raw satellite image (JPG/PNG) for detection & analysis |
| `GET` | `/satellite/image/result/{file}` | Retrieve annotated satellite output image |
| `GET` | `/drone/presets` | List drone evaluation videos (`test1.mp4`, `oil_tanker_drone.mp4`, etc.) |
| `POST` | `/drone/preset-video` | Run tracking, ConvNeXt classification, and Kalman projection on preset video |
| `POST` | `/drone/video` | Upload and process drone MP4 video |
| `GET` | `/drone/video/result/{file}` | Stream annotated tracked MP4 video |
| `POST` | `/surveillance/chat` | Context-aware AI maritime briefing chatbot via Groq |
| `GET` | `/rl/benchmarks` | PPO adaptive scheduler metrics vs standard baseline |
| `GET` | `/diagnostics/metrics` | Model evaluation precision, recall, and mAP metrics |

---

## 3. Models & Datasets Currently in Use

### A. Model Checkpoints (`models/weights/`):
| Model | Filename | Size | Purpose | Benchmark / Accuracy |
| :--- | :--- | :--- | :--- | :--- |
| **YOLO11n-VHRV** | `models/weights/vhrv_best.pt` | 5.45 MB | Satellite vessel detection | mAP50: 94.63%, Precision: 93.64%, Recall: 90.26% |
| **Custom YOLO** | `models/weights/vhrv_custom_best.pt` | 5.45 MB | Custom anchor-free baseline | mAP50: 96.84%, Precision: 96.12%, Recall: 93.45% |
| **ConvNeXt-Tiny** | `models/weights/convnext_tiny/best.pt` | 106.21 MB | Fine-grained 10-class ship classifier | Top-1 Test Accuracy: 81.56%, Macro F1: 81.32% |
| **ConvNeXt-Tiny (Last)**| `models/weights/convnext_tiny/last.pt` | 106.21 MB | Final epoch training checkpoint | - |
| **ResNet-18 (FGS-10)** | `models/weights/titanic_fgs10_resnet18_best.pt` | 44.81 MB | Comparative classifier baseline | Top-1 Test Accuracy: ~78.2% |
| **Florence-2-LoRA** | `models/weights/florence2_classifier_lora/` | 1.78 MB | Experimental VLM zero-shot classifier | 5-epoch Test Accuracy: 76.42% |
| **PPO Scheduler** | `models/weights/ppo_scheduler.zip` | 148 KB | Adaptive compute scheduling policy | Estimated 30-40% inference compute reduction |

### B. Datasets & Ground Truth Files (`data/`):
*Note: Datasets total ~7.3 GB and are stored outside git version control. Download these separately on new systems.*

1. **VHRV (Very High Resolution Vessel Dataset)**:
   - Path: `data/vhrv/vhrv/`
   - Config: `data/vhrv/vhrv/vhrv.yaml`
   - Splits: 1,052 train images, 300 validation images, 150 test images (~4800x2886 native resolution).
   - Format: YOLO format annotations (`images/` and `labels/`).
2. **TITANIC-FGS-10 Dataset**:
   - Path: `data/TITANIC-FGS-10/`
   - ImageNet format: `data/TITANIC-FGS-10/ImageNet/` (12,000 train, 1,285 validation, 1,285 test images across 10 classes).
   - Annotation JSON: `data/TITANIC-FGS-10/Instruction_train/ship_data_10class.json`.
3. **Drone Test Videos (`data/test_mp4/`)**:
   - `test1.mp4`: Royal Malaysian Navy Frigate KD Kasturi F25 patrol (743 frames, 30 FPS).
   - `oil_tanker_drone.mp4`: Commercial oil tanker open sea surveillance (655 frames, 30 FPS).
   - `cruise_ship_drone.mp4`: Allure of the Seas cruise ship surveillance (577 frames, 30 FPS).
   - `aircraft_carrier_drone.mp4`: Aircraft carrier flight deck operations (120 frames, 15 FPS).
   - `destroyer.mp4`: Naval destroyer operations (52.2 MB).

---

## 4. How the System is Currently Running

Both the backend and frontend are currently live and tested:

### 1. Backend Service:
- **Command**:
  ```powershell
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
  ```
- **Active Hardware**: NVIDIA GeForce RTX 3050 Laptop GPU (CUDA 12.6, PyTorch 2.14.0+cu126).
- **Health Verification**:
  ```powershell
  curl http://127.0.0.1:8000/health
  # Returns: {"status": "ok", "project": "OATrack-VLM"}
  ```

### 2. Frontend Application:
- **Command**:
  ```powershell
  cd frontend
  npm run dev
  ```
- **Port**: `http://localhost:5173/`
- **Features Tested & Passing**:
  - Full system telemetry dashboard (`/health`).
  - High-res satellite detection with Groq briefing (`/satellite`).
  - UAV continuous tracking with Hungarian association and annotated video export (`/tracking`).
  - Real-time VLM intelligence chatbot (`/intelligence`).
  - PPO adaptive compute benchmark analytics (`/ppo`).
  - Precision/Recall and mAP diagnostics (`/diagnostics`).
  - All 76 automated backend unit and integration test suites passing (`pytest tests/`).

---

## 5. Guide: Setting Up on a New System from GitHub

Follow these exact steps to clone the repository onto another machine, download datasets, and get everything running:

### Step 1: System Prerequisites
- **OS**: Windows 10/11 or Ubuntu 22.04+ LTS
- **Python**: Python 3.10.x (Recommended: 3.10.11)
- **Node.js**: v18.0.0+ or v20.0.0+ (with `npm` or `pnpm`)
- **CUDA** (Optional but recommended): NVIDIA GPU with CUDA 12.1+ / 12.6 support

### Step 2: Clone the Repository
```bash
git clone https://github.com/btprnikhil/Multimodal-Maritime-Surveillance-with-Kalman-Tracking-and-Vision-Language-Reasoning.git
cd Multimodal-Maritime-Surveillance-with-Kalman-Tracking-and-Vision-Language-Reasoning
```
*(If cloned into a wrapper folder, enter the `OATrack-VLM` directory where `requirements.txt` and `backend/` reside).*

### Step 3: Set Up Python Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

*Note on PyTorch with CUDA:* If using NVIDIA GPU on Windows:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your Groq API key:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
VHRV_MODEL_PATH=models/weights/vhrv_best.pt
CONFIDENCE_THRESHOLD=0.25
```

### Step 5: Download & Wire Datasets and Large Weights
Create the following directory layout in `OATrack-VLM/`:
```
OATrack-VLM/
├── data/
│   ├── vhrv/
│   │   └── vhrv/
│   │       ├── vhrv.yaml
│   │       ├── images/ (train, val, test)
│   │       └── labels/ (train, val, test)
│   ├── TITANIC-FGS-10/
│   │   ├── ImageNet/ (train, val, test 10 classes)
│   │   └── Instruction_train/ship_data_10class.json
│   ├── test_mp4/
│   │   ├── test1.mp4
│   │   ├── oil_tanker_drone.mp4
│   │   ├── cruise_ship_drone.mp4
│   │   └── aircraft_carrier_drone.mp4
│   └── results/
└── models/
    └── weights/
        ├── vhrv_best.pt
        ├── vhrv_custom_best.pt
        ├── convnext_tiny/
        │   ├── best.pt
        │   └── last.pt
        └── ppo_scheduler.zip
```
*(Download datasets from your team's cloud storage / Google Drive / HuggingFace repository and unpack into `data/`).*

### Step 6: Install Frontend Dependencies
```bash
cd frontend
npm install
# or: pnpm install
```
Ensure `frontend/.env` points to the backend:
```ini
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Step 7: Launch the Applications

**Terminal 1 (Backend API):**
```bash
# From OATrack-VLM root directory
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend UI):**
```bash
# From frontend directory
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser. All satellite presets, drone video tracking, and VLM surveillance intelligence will be fully functional.

### Step 8: Verify System Functionality
Run the comprehensive test suite to confirm all components are operational:
```bash
python -m pytest tests/
```
All 76 tests should pass with green status.
