# OATrack-VLM — Handover / Continue Prompt for a New Chatbot

Read this entire document, then verify current files with tools BEFORE changing anything.

====================================================================
1. PROJECT
====================================================================
Title: OATrack-VLM: Occlusion-Aware Tracking and Vision-Language
       Reasoning for Adaptive Maritime Surveillance

Root (Windows): F:\OATrack-VLM_complete_project\OATrack-VLM

Environment:
- Windows PowerShell, Python 3.10.11
- RTX 3050 Laptop GPU, 4 GB VRAM
- PyTorch 2.14.0+cu126, torchvision 0.29.0+cu126, torchaudio 2.11.0+cu126
- CUDA available = True
- Transformers 4.57.0, Ultralytics, timm, PEFT 0.21.0, Accelerate 1.15.0
- Streamlit 1.64.0, FastAPI 0.115.0 (backend currently works with it)
- NO .venv. Packages are global in the Python 3.10 install.

====================================================================
2. SYSTEM MODES (what the project claims)
====================================================================
A) SATELLITE MODE: satellite JPG/PNG -> YOLO11n vessel detection -> VLM
   natural-language briefing (Groq). HBB only (NOT OBB).
B) DRONE VIDEO MODE: MP4 -> frame-by-frame YOLO detection -> lightweight
   ByteTrack-STYLE tracker (NOT official ByteTrack) -> ConvNeXt-Tiny
   classification -> dashboard + processed JSON. Annotated video output
   NOT fully verified.
C) RL/PPO: NOT trained. Scheduler is deterministic/rule-based. Goal is
   estimated edge-compute/energy reduction on low-activity scenes.
   DO NOT claim UAV battery control.

====================================================================
3. DATASETS + MODELS
====================================================================
VHRV (satellite, HBB):
- path: data\vhrv\vhrv  (yaml: data\vhrv\vhrv\vhrv.yaml, nc=1 'vessel')
- train 1052 / val 300 / test 150 images, 10158 instances, ~4800x2886
Fine-tuned YOLO11n weights:
- runs\detect\runs\detect\vhrv_yolo11n_60ep2\weights\best.pt
Independent test set (150 img / 1191 instances):
- P 89.56%, R 84.31%, mAP50 89.57%, mAP50-95 64.55%
- (old baseline for comparison only: P .715, R .504, mAP50 .569, mAP50-95 .353)

TITANIC-FGS-10 (classification, 10 classes):
- Destroyer, Frigate, Aircraft_carrier, Amphibious_assault_ship, Cruiser,
  Littoral_combat_ship, Cruise_ship, Oil_tanker, Yacht, Non_ship
- data\TITANIC-FGS-10\ImageNet (train 12000, val 1285, test 1285)
- instruction JSON: data\TITANIC-FGS-10\Instruction_train\ship_data_10class.json
ConvNeXt-Tiny classifier (models\weights\convnext_tiny\best.pt/last.pt):
- 5-epoch test: acc 81.56%, P 81.48%, R 81.56%, F1 81.32%
- hard classes: Destroyer F1 .41, Frigate .61, Cruiser .63
Florence-2-base LoRA (models\weights\florence2_classifier_lora):
- experimental; 5-epoch acc 76.42%, 3-epoch 74.47%, eager attn,
  num_beams=1, use_cache=False

====================================================================
4. CODE (models/)
====================================================================
- detector.py: YOLO HBB detection. detector for satellite AND drone.
- classifier.py: ConvNeXt-Tiny 10-class vessel classifier.
- groq_vlm.py: VLM briefing via Groq API.
- backend/main.py: FastAPI app. Endpoints:
    GET  /health
    POST /satellite/detect
    POST /drone/video
- tracking/tracker.py: lightweight ByteTrack-STYLE HBB tracker
    (center-distance association, greedy 1-to-1 matching, max dist ~100px,
     track IDs, age, missed, vx/vy, detection_index, matched_detection)
    NO OBB, NO bbox IoU, NO size-similarity. A single ship can fragment
    into multiple IDs. This is a KNOWN limitation; improve only after the
    frontend/backend are stable.
- frontend/app.py: Streamlit dashboard.

Important CURRENT behaviors in the ORCHESTRATOR (backend/main.py):
- satellite_detect returns keys: status, mode, image_path, ship_count,
  detections, vlm_analysis.
- It does NOT return "ship_present" or "drone_target".
  Frontend MUST use: "YES" if satellite_result.get("ship_count", 0) > 0
  (current app.py already does this correctly).
- drone result keys (verified earlier): status, mode, video_path, fps,
  frame_count, processed_frames, resolution, status_message,
  unique_track_count, total_detections, average_detections_per_frame,
  processing_mode_counts, final_track_classifications, track_summaries,
  primary_vessel, frames.
- annotated_video_path / annotated_video_url / annotation_error exist in
  frontend code branches but were NOT verified to actually be produced by
  the orchestrator. INSPECT backend/main.py BEFORE assuming animated
  video works. Do not claim it works until verified.

====================================================================
5. KNOWN FIXES / GOTCHAS (do not regress)
====================================================================
1) Backend startup crash "Router.__init__() got an unexpected keyword
   argument 'on_startup'" was fixed by making Starlette version compatible
   with FastAPI 0.115.0. Backend starts fine now. Do not change the
   version coupling unnecessarily.
2) Frontend st.image() must NOT use use_container_width or
   use_column_width (both raised TypeError in `st.image` with this
   Streamlit). Use: st.image(satellite_file, caption="...") only.
3) Do NOT paste PowerShell commands into app.py (happened before).
4) Streamlit "Failed to fetch dynamically imported module Metric.*.js"
   + blank white screen: BROWSER-side stale cache/service-worker. Server
   verified healthy (HTML serves, _stcore/health returns 200 'ok',
   entrypoint index.CcFifQPt.js loads). Fix = open in incognito
   (Ctrl+Shift+N) or hard refresh Ctrl+Shift+R / fresh tab.

====================================================================
6. VERIFIED TEST RESULTS (as of 17-Sep-2026 session)
====================================================================
- Backend /health previously 200 OK; satellite/detect on VHRV test image
  vhrv_00038.jpg returned: status=success, ship_count=3, 3 detections,
  first det confidence 0.9412, bbox present, vlm_analysis present.
- Example older drone oil-tanker run (30 fps, 658 frames, 27 unique
  tracks, total detections 311): Track 26 = Oil tanker, 75 observations,
  100% stability, expected primary vessel. Tanker fragmented across IDs
  (Track 1 yacht, Track 2/3/21/22 oil tanker, Track 4/24 cruiser, etc.).
- Cruise video older run (580 frames, 15 tracks, 261 detections):
  classification NOT yet re-verified; do not claim.

====================================================================
7. CURRENT RUNNING STATE
====================================================================
AS OF the handover creation (~17-Sep-2026 16:37 local):
- Backend: NOT running (user closed it).
- Streamlit: NOT running (user closed it).
A new session must start both (see section 8).

====================================================================
8. EXACT START COMMANDS
====================================================================
Backend (PowerShell window 1):
cd "F:\OATrack-VLM_complete_project\OATrack-VLM"
python -m uvicorn backend.main:app
# expect "Uvicorn running on http://127.0.0.1:8000" and
# "Application startup complete." -> http://127.0.0.1:8000/health = 200

Frontend (PowerShell window 2):
cd "F:\OATrack-VLM_complete_project\OATrack-VLM"
python -m streamlit run frontend/app.py
# open http://localhost:8501 (use incognito / fresh tab if blank)

====================================================================
9. REMAINING WORK / PRIORITY ORDER (follow this)
====================================================================
1. Start backend + frontend (section 8).
2. Confirm dashboard loads (incognito if blank).
3. Test satellite upload; confirm:
   - Ship Present = YES when ship_count > 0 (frontend now reads ship_count)
   - Vessels Detected = actual YOLO count
   - Show detection boxes/results from satellite_result detections.
4. Test drone MP4; verify tracking + classification output keys.
5. Verify annotated video if implemented (inspect backend/main.py first;
   currently unverified).
6. THEN improve tracker continuity (add bbox IoU matching, bbox
   size/aspect-ratio similarity, better continuity logic) to fix
   fragmented single-ship-into-multiple-IDs problem.
7. ONLY after all of the above: move to RL/PPO (reduced processing for
   low-activity scenes; estimated edge compute/energy reduction claim
   only). Do NOT train PPO now.
- Do NOT restart completed training or redesign architecture.

====================================================================
10. WORK STYLE (required)
====================================================================
- Verify before modifying. Inspect the actual current file first.
- Exact PowerShell commands and exact file paths.
- Minimal explanation; step-by-step.
- Do not change multiple unrelated files at once.
- After every fix, tell the user exactly how to test it.
- Do not claim something is implemented unless actually verified.
- NEVER commit unless explicitly asked.

====================================================================
11. ONE-LINE PRESENTATION NARRATIVE (approved wording)
====================================================================
"Satellite imagery gives wide-area initial vessel detection. The system
then supports drone video analysis: YOLO detects vessels frame-by-frame,
tracking maintains identities over time, and ConvNeXt classifies vessel
type. The RL/PPO component will later adapt processing effort to scene
activity so low-activity/empty-sea periods can use reduced computation
instead of continuously running expensive processing."
Do NOT say the system physically controls a drone battery.