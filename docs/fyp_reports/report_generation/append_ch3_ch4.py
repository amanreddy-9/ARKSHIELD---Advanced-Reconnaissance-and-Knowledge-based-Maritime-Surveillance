# append_ch3_ch4.py - Append Chapter 3 & 4 to report_sections.py

content = '''
CH3_DATA_METHOD = {
    "title": "DATASET AND PROPOSED METHODOLOGY",
    "num": "3",
    "intro": (
        "An effective autonomous maritime surveillance framework requires robust datasets that capture the extreme "
        "spatial scale disparities of spaceborne remote sensing as well as the fine-grained visual characteristics of "
        "naval vessels observed from tactical aerial platforms. This chapter details the two core datasets utilized in "
        "this project—the VHRV optical satellite benchmark and the TITANIC-FGS-10 fine-grained vessel classification dataset—alongside "
        "the mathematical and algorithmic formulation of the proposed OATrack-VLM methodology."
    ),
    "s3_1": (
        "3.1 VHRV Optical Satellite Benchmark Dataset",
        "Strategic satellite vessel detection is evaluated on the Very-High-Resolution Vessel (VHRV) optical satellite benchmark [9]. "
        "VHRV comprises 1,502 wide-area scenes containing 10,158 authentic annotated vessel instances, with native image dimensions "
        "typically spanning 4800x2886 pixels. The dataset captures diverse maritime operating conditions, including deep ocean waters, "
        "coastal shorelines, commercial anchorages, and dense harbor terminals under varying sun glint and sea state conditions.\\n\\n"
        "To ensure scientific rigor and prevent data leakage, the dataset is partitioned into 1,052 training images (7,125 vessels), "
        "300 validation images (1,842 vessels), and an independent held-out test split of 150 images containing 1,191 vessels, as summarized in Table 3.1. "
        "Ground truth annotations are preserved as authentic horizontal bounding boxes (HBB, [x_center, y_center, width, height])."
    ),
    "s3_2": (
        "3.2 TITANIC-FGS-10 Maritime Classification Dataset",
        "Tactical vessel categorization is evaluated on TITANIC-FGS-10, curated from the TITANIC-FGS benchmark [12] across ten maritime "
        "vessel categories. The dataset comprises 14,570 annotated vessel crops partitioned into 12,000 training images (1,200 per class), "
        "1,285 validation images, and 1,285 independent test images, as summarized in Table 3.2. The ten classes encompass combatants "
        "(Destroyer, Frigate, Cruiser, Aircraft Carrier, Amphibious Assault Ship, Littoral Combat Ship), commercial craft (Oil Tanker, "
        "Cruise Ship), civilian vessels (Yacht), and background non-ship clutter (piers, wave breaks)."
    ),
    "s3_3": (
        "3.3 Data Preprocessing and Ground-Truth Integrity Verification",
        "Satellite images undergo spatial preprocessing to eliminate downsampling truncation. Traditional pipelines aggressively resize "
        "4800x2886 scenes to 640x640 pixels, reducing small vessels (30–60 meters) to fewer than 5 pixels, causing feature collapse. "
        "In OATrack-VLM, images are processed at 1024x1024 pixels, preserving fine vessel hulls while maintaining real-time latency. "
        "Data integrity audits verify that all ground-truth bounding box coordinates remain within valid unit intervals [0, 1]. "
        "Augmentations during detector training include random horizontal flips, mosaic synthesis, and HSV color jitter, while classification "
        "crops undergo random rotations (±15°) and color jitter."
    ),
    "s3_4": (
        "3.4 Strategic Satellite-Based Vessel Detection (YOLO11n @ 1024px)",
        "Wide-area optical imagery is processed through a fine-tuned YOLO11n detector operating at 1024x1024 resolution. YOLO11n utilizes "
        "a lightweight convolutional backbone with optimized C3k2 blocks and spatial pyramid pooling (SPPF). For an input image I_sat, the model "
        "outputs bounding box coordinates (x1, y1, x2, y2), confidence score s in [0, 1], and centroid (cx, cy) with dimensions (w, h). "
        "Non-maximum suppression (NMS) with confidence threshold tau_conf = 0.25 and IoU threshold tau_iou = 0.60 suppresses redundant overlaps."
    ),
    "s3_5": (
        "3.5 Target Handoff Adapter Architecture",
        "Upon positive satellite detection, target coordinates and bounding geometries are packaged into a structured surveillance cue: "
        "M_handoff = {N_vessels, {(cx_i, cy_i, w_i, h_i, s_i)}}. A software-in-the-loop simulation adapter transforms these pixel coordinates "
        "into simulated geographic waypoints to seed tactical UAV flight paths. The UAV enters the sector and initiates continuous video observation, "
        "eliminating costly open-ocean transit searches."
    ),
    "s3_6": (
        "3.6 Tactical UAV Tracking via Discrete Linear Kalman Filter",
        "To preserve target identities across continuous drone video feeds without ID switching, tracking is formulated as an 8-state discrete "
        "linear dynamical system. Each active track maintains state vector x = [cx, cy, w, h, vx, vy, vw, vh]^T in R^8, modeling centroid coordinates, "
        "bounding box dimensions, translational velocities (vx, vy), and scale evolution rates (vw, vh). The measurement vector is z = [cx, cy, w, h]^T in R^4.\\n\\n"
        "Assuming a constant-velocity transition model with time step Delta_t = 1, state prediction follows:\\n"
        "x_hat_t^- = F * x_{t-1},    P_t^- = F * P_{t-1} * F^T + Q,\\n"
        "where state transition matrix F = [I_4, I_4; 0_4, I_4] and Q is the process noise covariance modeling camera jitter and maneuvers. "
        "Upon associating measurement z_t, state and covariance updates follow:\\n"
        "K_t = P_t^- * H^T * (H * P_t^- * H^T + R)^(-1),\\n"
        "x_t = x_hat_t^- + K_t * (z_t - H * x_hat_t^-),\\n"
        "P_t = (I - K_t * H) * P_t^- * (I - K_t * H)^T + K_t * R * K_t^T,\\n"
        "where measurement matrix H = [I_4, 0_4], and the Joseph-form covariance update guarantees numerical positive semi-definiteness.\\n\\n"
        "Data association employs a multi-feature affinity cost C(i, j) combining bounding-box IoU, normalized centroid distance, size similarity, "
        "and motion heading:\\n"
        "C(i, j) = w1 * (1 - IoU) + w2 * (d_ij / d_max) + w3 * (1 - S_size) + w4 * C_motion.\\n"
        "Matching executes in three hierarchical stages: active tracks match high-confidence detections (s >= 0.40); unmatched active tracks match "
        "low-confidence detections (0.15 <= s < 0.40) for occlusion recovery; and remaining detections re-identify coasting tracks (missed up to 45 frames). "
        "Sub-part containment suppression filters out detections whose area overlap exceeds 60% inside an existing confirmed vessel hull."
    ),
    "s3_7": (
        "3.7 Fine-Grained Vessel Classification and Temporal Evidence Aggregation",
        "For confirmed tracks, context-expanded vessel crops (20% margin) are resized to 224x224 and classified across 10 categories via ConvNeXt-Tiny. "
        "To mitigate transient wave obscuration and viewpoint fluctuations, evidence is aggregated across track lifetime T:\\n"
        "E_k(T) = sum(s_i * P(y = k | X_i)) / sum(s_i),    y_hat(T) = argmax_k E_k(T),\\n"
        "where s_i is detection confidence for frame i. Temporal consensus stabilizes classifications, lifting final track accuracy above 90%."
    ),
    "s3_8": (
        "3.8 PPO Adaptive Compute Scheduling and Edge Optimization",
        "To extend UAV battery endurance, an edge Gymnasium environment encapsulates drone operational state into an 8D observation vector: "
        "o = [o_vis, o_det, o_avg, o_track, o_mot, o_conf, o_act, o_prog]^T in [0, 1]^8. The discrete action space A in {0: LOW (1/4 fps, cost 0.25), "
        "1: NORMAL (1/2 fps, cost 0.50), 2: HIGH (full fps, cost 1.00)} balances tracking awareness against compute cost via reward:\\n"
        "R(s, a) = R_aware(s, a) - 0.35 * c_a.\\n"
        "An operational safety override deterministically enforces a_eff >= 1 whenever a target is detected or confidence >= 0.70, and sets a_eff = 2 "
        "for multi-track encounters, preventing target loss during critical handoffs."
    ),
    "s3_9": (
        "3.9 Grounded Vision-Language Reasoning Architecture",
        "The final tier converts numerical tracking telemetry and visual crops into grounded natural-language intelligence briefings using Groq-hosted "
        "Qwen-2.5-Vision and Llama-3.3-70B models. Sensor telemetry (vessel counts, Track IDs, bounding boxes, classification probabilities) is passed "
        "directly into structured prompt templates. The schema strictly restricts unobservable inferences, preventing hallucinations regarding vessel "
        "nationality, registration codes, or weapon armaments."
    )
}

CH4_SYS_DESIGN = {
    "title": "SYSTEM DESIGN AND ARCHITECTURE",
    "num": "4",
    "intro": (
        "The OATrack-VLM framework is designed as a modular, scalable, multi-tier autonomous maritime surveillance system. "
        "The architecture bridges spaceborne remote sensing, edge-optimized tactical aerial tracking, deep convolutional classification, "
        "reinforcement learning compute control, and grounded multimodal language synthesis. This chapter outlines the overall system "
        "architecture, data flow pipeline, surveillance workflow, application layering, and major system components."
    ),
    "s4_1": (
        "4.1 Overall System Architecture",
        "The system architecture organizes maritime perception across three functional tiers: strategic wide-area satellite localization, "
        "tactical aerial tracking with adaptive edge-compute scheduling, and semantic intelligence synthesis, as illustrated in Figure 4.1.\\n\\n"
        "1. Strategic Satellite Tier: High-resolution YOLO11n processes wide-area satellite images at 1024x1024 pixels, detecting surface vessels "
        "and extracting bounding boxes without downsampling truncation.\\n"
        "2. Tactical UAV Tier: A target handoff adapter translates satellite coordinates into localized UAV search sectors. The drone ingests sequential "
        "video feeds, where an 8-state discrete linear Kalman filter maintains persistent vessel tracks under continuous multi-feature association "
        "and sub-part suppression. Concurrently, a Gymnasium-trained PPO scheduler dynamically throttles inference rates with safety overrides.\\n"
        "3. Semantic Intelligence Tier: Confirmed tracks are categorized across 10 classes using ConvNeXt-Tiny with temporal evidence aggregation. "
        "A grounded vision-language reasoning layer synthesizes telemetry-verified tactical briefings via Groq API, rendered on a Streamlit operations console."
    ),
    "s4_2": (
        "4.2 Data Flow Pipeline",
        "The end-to-end data flow operates through the following formal sequence:\\n"
        "I_sat -> YOLO11n -> D_vessel -> Target Handoff -> T_UAV -> PPO Throttling -> Kalman Filter -> T_id -> ConvNeXt-Tiny -> C_stable -> Groq VLM -> R_intel.\\n\\n"
        "1. Satellite Ingestion: Wide-area optical scenes are normalized and tiled to 1024x1024 pixels.\\n"
        "2. Satellite Detection: YOLO11n generates bounding boxes D_vessel = {(c_x, c_y, w, h, s)}.\\n"
        "3. Target Handoff: Target coordinates seed tactical UAV flight paths.\\n"
        "4. UAV Video Stream: Drone camera frames are sampled dynamically according to PPO action a in {LOW, NORMAL, HIGH}.\\n"
        "5. Kalman Tracking: States x_t and covariances P_t are updated, assigning persistent Track IDs T_id.\\n"
        "6. Classification & Aggregation: Context crops are evaluated by ConvNeXt-Tiny and temporally aggregated into C_stable.\\n"
        "7. Intelligence Generation: Verified telemetry is formatted into natural-language intelligence briefing R_intel."
    ),
    "s4_3": (
        "4.3 Surveillance Processing Workflow",
        "The surveillance processing workflow encompasses six primary operational steps:\\n"
        "1. Wide-Area Acquisition: Satellite scene acquisition and automated high-resolution YOLO11n inference.\\n"
        "2. Spatial Coordinate Handoff: Autonomous packaging of target centroids and vessel count cues.\\n"
        "3. Tactical Drone Ingestion: Video stream decoding (MP4/AVI) and PPO compute scheduling evaluation.\\n"
        "4. State Estimation & Association: Constant-velocity Kalman prediction, multi-feature Hungarian matching, and sub-part containment filtering.\\n"
        "5. Evidence Consensus: Multi-frame probability integration over track lifetimes.\\n"
        "6. Briefing Synthesis: Grounded vision-language intelligence reporting and real-time operator HUD rendering."
    ),
    "s4_4": (
        "4.4 Proposed Application Architecture",
        "The operational software implementation is organized into three distinct tiers:\\n"
        "1. Presentation Layer (Maritime Surveillance Command Center): Built using Streamlit, providing real-time video playback with trajectory trails, "
        "interactive HUD telemetry cards, satellite overlays, and intelligence briefing panels.\\n"
        "2. AI Inference Engine & Processing Layer: Houses the YOLO11n detector wrapper, 8-state Kalman tracking engine, ConvNeXt-Tiny classifier, "
        "PPO scheduler policy, and Groq VLM API client.\\n"
        "3. Telemetry & Data Layer: Implemented via FastAPI, providing RESTful endpoints (/satellite/detect, /drone/video, /health) and JSON telemetry logging."
    ),
    "s4_5": (
        "4.5 Major System Components",
        "The core functional components of the OATrack-VLM framework are summarized in Table 4.1."
    )
}
'''

with open(r'f:\OATrack-VLM_complete_project\report_sections.py', 'a', encoding='utf-8') as f:
    f.write(content)

print('Appended Chapters 3 & 4 successfully!')
