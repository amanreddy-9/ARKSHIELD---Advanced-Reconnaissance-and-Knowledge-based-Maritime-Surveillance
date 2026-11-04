from pathlib import Path
import shutil
import tempfile
import json
import torch

from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline.orchestrator import OATrackPipeline
from models.detector import ModelLoadError

BASE_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(
    title="OATrack-VLM API",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite defaults to localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ModelLoadError)
async def model_load_error_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


pipeline = OATrackPipeline()

# Mount static asset folders for presets and diagnostics if present
outputs_dir = BASE_DIR / "outputs"
if outputs_dir.exists():
    app.mount("/static/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")

data_dir = BASE_DIR / "data"
if data_dir.exists():
    app.mount("/static/data", StaticFiles(directory=str(data_dir)), name="data")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "OATrack-VLM"
    }


@app.get("/system/health")
def system_health():
    """Detailed health telemetry for all AI/ML subsystems."""
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Fallback)"

    return {
        "status": "ok",
        "project": "OATrack-VLM",
        "backend": {
            "service": "FastAPI",
            "version": "1.0.0",
            "status": "online"
        },
        "hardware": {
            "device": device_name,
            "cuda_available": cuda_available,
            "torch_version": torch.__version__,
        },
        "subsystems": {
            "detector": {
                "name": "YOLO11n-VHRV High-Res Detector",
                "status": "online" if hasattr(pipeline, "detector") and pipeline.detector else "offline",
                "default_imgsz": 1024,
            },
            "tracker": {
                "name": "Continuous Kalman Tracker (IoU + Centroid + Aspect + Motion)",
                "status": "online" if hasattr(pipeline, "tracker") and pipeline.tracker else "offline",
            },
            "classifier": {
                "name": "ConvNeXt-Tiny Fine-Grained Classifier (TITANIC-FGS-10)",
                "status": "online" if hasattr(pipeline, "classifier") and pipeline.classifier else "offline",
            },
            "scheduler": {
                "name": "Gymnasium PPO Adaptive Compute Policy + Safety Override",
                "status": "online" if hasattr(pipeline, "scheduler") and pipeline.scheduler else "offline",
            },
            "vlm": {
                "name": "Groq Vision",
                "availability": pipeline.vlm.availability(),
                "status": "online" if pipeline.vlm.availability()["status"] == "ready" else "unavailable",
            }
        }
    }


# ============================================================
# SATELLITE DETECTION
# ============================================================

SATELLITE_PRESETS = {
    "frigate_optical": {
        "id": "frigate_optical",
        "name": "Naval Frigate KD Kasturi F25 (Optical Aerial)",
        "path": "outputs/diagnostics/test1_frames/f_0360.jpg",
        "static_url": "/static/outputs/diagnostics/test1_frames/f_0360.jpg",
        "vessel_hint": "1 Frigate",
    },
    "dense_harbor": {
        "id": "dense_harbor",
        "name": "Dense Harbor Anchorage (89 vessels) - vhrv_01305.jpg",
        "path": "data/vhrv/vhrv/images/test/vhrv_01305.jpg",
        "static_url": "/static/data/vhrv/vhrv/images/test/vhrv_01305.jpg",
        "vessel_hint": "89 Vessels",
    },
    "offshore_convoy": {
        "id": "offshore_convoy",
        "name": "Offshore Convoy (19 vessels) - vhrv_01045.jpg",
        "path": "data/vhrv/vhrv/images/test/vhrv_01045.jpg",
        "static_url": "/static/data/vhrv/vhrv/images/test/vhrv_01045.jpg",
        "vessel_hint": "19 Vessels",
    },
    "coastal_harbor": {
        "id": "coastal_harbor",
        "name": "Coastal Harbor (3 vessels) - vhrv_00038.jpg",
        "path": "data/vhrv/vhrv/images/test/vhrv_00038.jpg",
        "static_url": "/static/data/vhrv/vhrv/images/test/vhrv_00038.jpg",
        "vessel_hint": "3 Vessels",
    },
    "harbor_approach": {
        "id": "harbor_approach",
        "name": "Harbor Approach (2 vessels) - vhrv_00050.jpg",
        "path": "data/vhrv/vhrv/images/test/vhrv_00050.jpg",
        "static_url": "/static/data/vhrv/vhrv/images/test/vhrv_00050.jpg",
        "vessel_hint": "2 Vessels",
    },
    "single_large": {
        "id": "single_large",
        "name": "Single Large Vessel - vhrv_00001.jpg",
        "path": "data/vhrv/vhrv/images/train/vhrv_00001.jpg",
        "static_url": "/static/data/vhrv/vhrv/images/train/vhrv_00001.jpg",
        "vessel_hint": "1 Large Vessel",
    },
}

@app.get("/satellite/presets")
def get_satellite_presets():
    """List preset satellite imagery targets available on server."""
    presets = []
    for k, v in SATELLITE_PRESETS.items():
        full_p = BASE_DIR / v["path"]
        presets.append({
            "id": k,
            "name": v["name"],
            "vessel_hint": v["vessel_hint"],
            "exists": full_p.exists(),
            "preview_url": v["static_url"] if full_p.exists() else None,
        })
    return {"presets": presets}


class SatellitePresetRequest(BaseModel):
    preset_id: str
    weights: Optional[str] = None
    conf: Optional[float] = 0.25
    iou: Optional[float] = 0.60


@app.post("/satellite/detect-preset")
async def satellite_detect_preset(req: SatellitePresetRequest):
    """Run detection on a preset satellite image without re-uploading file bytes."""
    preset = SATELLITE_PRESETS.get(req.preset_id)
    if not preset:
        return {"status": "error", "message": f"Preset '{req.preset_id}' not found."}

    img_path = BASE_DIR / preset["path"]
    if not img_path.exists():
        return {"status": "error", "message": f"Preset image file not found on disk: {preset['path']}"}

    result = pipeline.satellite_detect(
        str(img_path),
        weights=req.weights,
        conf=req.conf,
        iou=req.iou
    )
    annotated_path = result.get("annotated_image_path")
    if annotated_path:
        result["annotated_image_url"] = (
            "/satellite/image/result/" + Path(annotated_path).name
        )
    result["raw_image_url"] = preset["static_url"]
    return result


@app.post("/satellite/detect")
async def satellite_detect(
    file: UploadFile = File(...),
    weights: Optional[str] = Form(None),
    conf: Optional[float] = Form(0.25),
    iou: Optional[float] = Form(0.60),
):
    suffix = Path(file.filename or ".jpg").suffix or ".jpg"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tmp:
        shutil.copyfileobj(file.file, tmp)
        path = tmp.name

    try:
        result = pipeline.satellite_detect(path, weights=weights, conf=conf, iou=iou)
        annotated_path = result.get("annotated_image_path")
        if annotated_path:
            result["annotated_image_url"] = (
                "/satellite/image/result/" + Path(annotated_path).name
            )
        return result
    finally:
        Path(path).unlink(missing_ok=True)


# ============================================================
# DRONE VIDEO
# ============================================================

DRONE_PRESETS = {
    "frigate_patrol": {
        "id": "frigate_patrol",
        "name": "Naval Frigate Patrol (KD Kasturi F25)",
        "path": "data/test_mp4/test1.mp4",
        "static_url": "/static/data/test_mp4/test1.mp4",
        "vessel_hint": "Frigate F25",
    },
    "oil_tanker": {
        "id": "oil_tanker",
        "name": "Oil Tanker Surveillance Footage",
        "path": "data/test_mp4/oil_tanker_drone.mp4",
        "static_url": "/static/data/test_mp4/oil_tanker_drone.mp4",
        "vessel_hint": "Oil Tanker",
    },
    "cruise_ship": {
        "id": "cruise_ship",
        "name": "Cruise Ship (Allure of the Seas)",
        "path": "data/test_mp4/cruise_ship_drone.mp4",
        "static_url": "/static/data/test_mp4/cruise_ship_drone.mp4",
        "vessel_hint": "Cruise Ship",
    },
    "aircraft_carrier": {
        "id": "aircraft_carrier",
        "name": "USS Gerald R. Ford Simulation",
        "path": "data/test_mp4/aircraft_carrier_drone.mp4",
        "static_url": "/static/data/test_mp4/aircraft_carrier_drone.mp4",
        "vessel_hint": "Aircraft Carrier",
    },
}

@app.get("/drone/presets")
def get_drone_presets():
    """List preset UAV video feeds available on server."""
    presets = []
    for k, v in DRONE_PRESETS.items():
        full_p = BASE_DIR / v["path"]
        presets.append({
            "id": k,
            "name": v["name"],
            "vessel_hint": v["vessel_hint"],
            "exists": full_p.exists(),
            "video_url": v["static_url"] if full_p.exists() else None,
        })
    return {"presets": presets}


class DronePresetRequest(BaseModel):
    preset_id: str
    target_x: Optional[float] = 0.0
    target_y: Optional[float] = 0.0
    sample_every: Optional[int] = 2
    max_frames: Optional[int] = None


@app.post("/drone/preset-video")
async def drone_preset_video(req: DronePresetRequest):
    """Run tracking directly on a preset UAV video without uploading large files."""
    preset = DRONE_PRESETS.get(req.preset_id)
    if not preset:
        return {"status": "error", "message": f"Preset '{req.preset_id}' not found."}

    vid_path = BASE_DIR / preset["path"]
    if not vid_path.exists():
        return {"status": "error", "message": f"Preset video file not found on disk: {preset['path']}"}

    result = pipeline.drone_video(
        str(vid_path),
        req.target_x or 0.0,
        req.target_y or 0.0,
        sample_every=req.sample_every or 2,
        max_frames=req.max_frames,
        original_name=preset["name"]
    )

    annotated_path = result.get("annotated_video_path")
    if annotated_path:
        result["annotated_video_url"] = (
            "/drone/video/result/" + Path(annotated_path).name
        )
    return result


@app.post("/drone/video")
async def drone_video(
    file: UploadFile = File(...),
    target_x: float = Form(0),
    target_y: float = Form(0),
    sample_every: int = Form(2)
):
    suffix = Path(file.filename or ".mp4").suffix or ".mp4"

    if suffix.lower() not in [".mp4", ".avi", ".mov", ".mkv"]:
        return {
            "status": "error",
            "message": "Please upload a valid drone video."
        }

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tmp:
        shutil.copyfileobj(file.file, tmp)
        path = tmp.name

    try:
        result = pipeline.drone_video(
            path,
            target_x,
            target_y,
            sample_every=sample_every,
            original_name=file.filename
        )

        annotated_path = result.get("annotated_video_path")
        if annotated_path:
            result["annotated_video_url"] = (
                "/drone/video/result/"
                + Path(annotated_path).name
            )

        return result
    finally:
        Path(path).unlink(missing_ok=True)


# ============================================================
# SURVEILLANCE CHAT (VLM)
# ============================================================

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    context: Optional[str] = ""

@app.post("/surveillance/chat")
async def surveillance_chat(req: ChatRequest):
    reply = pipeline.vlm.chat(
        user_message=req.message,
        chat_history=req.history or [],
        context_data=req.context or ""
    )
    return {"reply": reply}


# ============================================================
# RESULT FILE SERVING
# ============================================================

@app.get("/drone/video/result/{filename}")
def drone_video_result(filename: str):
    results_dir = BASE_DIR / "data" / "results"
    safe_name = Path(filename).name
    path = results_dir / safe_name

    if not path.is_file() or path.suffix.lower() != ".mp4":
        return {
            "status": "error",
            "message": "Annotated video not found."
        }

    return FileResponse(
        path=str(path),
        media_type="video/mp4",
        filename=path.name
    )


@app.get("/satellite/image/result/{filename}")
def satellite_image_result(filename: str):
    results_dir = BASE_DIR / "data" / "results"
    safe_name = Path(filename).name
    path = results_dir / safe_name

    if not path.is_file() or path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        return {
            "status": "error",
            "message": "Annotated image not found."
        }

    media = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(
        path=str(path),
        media_type=media,
        filename=path.name
    )


# ============================================================
# PPO RL & ANALYTICS HELPER ENDPOINTS
# ============================================================

@app.get("/rl/benchmarks")
def get_rl_benchmarks():
    """Retrieve PPO adaptive compute benchmark data."""
    bench_file = BASE_DIR / "outputs" / "rl" / "scheduler_comparison_metrics.json"
    if bench_file.exists():
        try:
            with open(bench_file, "r") as f:
                return json.load(f)
        except Exception as exc:
            return {"error": str(exc)}
    return {}


@app.get("/rl/history")
def get_rl_history():
    """Retrieve live chronological mission history."""
    hist_file = BASE_DIR / "outputs" / "rl" / "live_mission_history.json"
    if hist_file.exists():
        try:
            with open(hist_file, "r") as f:
                return json.load(f)
        except Exception as exc:
            return {"error": str(exc)}
    return []


# ============================================================
# DIAGNOSTICS & LOSS METRICS ENDPOINTS
# ============================================================

@app.get("/diagnostics/metrics")
def get_diagnostics_metrics():
    """Retrieve detector evaluation metrics for Baseline 1024px and Custom 1024px."""
    m_1024_file = BASE_DIR / "outputs" / "diagnostics" / "metrics_vhrv_best_1024px.json"
    m_custom_file = BASE_DIR / "outputs" / "diagnostics" / "metrics_vhrv_custom_best_1024px.json"
    loss_summary_file = BASE_DIR / "outputs" / "training_loss_summary.json"

    data = {
        "baseline_1024": {},
        "custom_1024": {},
        "loss_summary": {},
    }

    if m_1024_file.exists():
        try:
            with open(m_1024_file, "r") as f:
                data["baseline_1024"] = json.load(f)
        except Exception:
            pass

    if m_custom_file.exists():
        try:
            with open(m_custom_file, "r") as f:
                data["custom_1024"] = json.load(f)
        except Exception:
            pass

    if loss_summary_file.exists():
        try:
            with open(loss_summary_file, "r") as f:
                data["loss_summary"] = json.load(f)
        except Exception:
            pass

    return data


@app.get("/diagnostics/samples")
def get_diagnostics_samples():
    """List diagnostic verification sample images."""
    diag_dir = BASE_DIR / "outputs" / "diagnostics" / "ground_truth_vs_prediction"
    multi_dir = BASE_DIR / "outputs" / "diagnostics" / "multi_ship_tests"

    samples = []
    if diag_dir.exists():
        for p in diag_dir.glob("*.jpg"):
            samples.append({
                "name": p.name,
                "category": "Ground Truth vs Prediction",
                "url": f"/static/outputs/diagnostics/ground_truth_vs_prediction/{p.name}"
            })

    if multi_dir.exists():
        for p in multi_dir.glob("*.jpg"):
            samples.append({
                "name": p.name,
                "category": "Multi-Ship Moorings",
                "url": f"/static/outputs/diagnostics/multi_ship_tests/{p.name}"
            })

    return {"samples": samples}
