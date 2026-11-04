# append_ch7_ch10.py - Append Chapters 7, 8, 9, 10 and Tables to report_sections.py

content = '''
CH7_TESTING = {
    "title": "EXPERIMENTAL RESULTS",
    "num": "7",
    "intro": (
        "This chapter documents the systematic verification and testing procedures conducted on the OATrack-VLM "
        "system prototype, validating component-level reliability and end-to-end integration across realistic "
        "maritime operational test cases."
    ),
    "s7_1": (
        "7.1 System Testing",
        "The integrated software prototype was subjected to rigorous test cases evaluating satellite ingestion, target handoff, "
        "video decoding, Kalman tracking persistence, deck containment filtering, classification consensus, PPO scheduling, "
        "and vision-language reporting. Table 7.1 details the test case specifications, expected results, observed outputs, and validation status."
    ),
    "s7_2": (
        "7.2 Current Achievements",
        "The primary accomplishments achieved in this project include:\\n"
        "• High-Resolution Satellite Benchmark: Achieved 93.64% precision, 90.26% recall, and 94.63% mAP@50 on the VHRV test split (150 images, 1,191 vessels).\\n"
        "• Elimination of Downsampling Truncation: Preserved fine-grained feature representation for small surface vessels beneath 60 meters.\\n"
        "• Autonomous Coordinate Handoff: Engineered software-in-the-loop adapter eliminating open-ocean search transits.\\n"
        "• Robust Discrete Linear Kalman Tracker: Designed 8-state tracking framework maintaining persistent tracks across occlusions.\\n"
        "• 100% Deck False Alarm Suppression: Successfully suppressed internal sub-part detections using geometric containment filtering.\\n"
        "• Track Fragmentation Reduction: Reduced track fragmentation from 27 spurious IDs to 2 on representative drone video feeds.\\n"
        "• Fine-Grained Vessel Classifier: Trained ConvNeXt-Tiny on TITANIC-FGS-10, attaining 81.56% top-1 accuracy and 82.84% macro F1.\\n"
        "• Gymnasium PPO Adaptive Scheduler: Developed RL environment and trained PPO agent saving 75% compute on empty seas and 45.46% to 52.12% on active missions.\\n"
        "• Operational Safety Override: Enforced deterministic protection ensuring zero target loss during tactical encounters.\\n"
        "• Grounded VLM Telemetry Briefings: Integrated Groq Qwen-2.5-Vision and Llama-3.3-70B models with zero factual hallucinations.\\n"
        "• Deployed Command Center Console: Built operational Streamlit dashboard backed by high-throughput FastAPI REST services."
    ),
    "s7_3": (
        "7.3 Limitations",
        "To preserve scientific integrity, several operational boundaries are explicitly documented:\\n"
        "• Horizontal Bounding Box Constraint: The current system operates on Horizontal Bounding Boxes (HBB) as defined by VHRV. Diagonal vessels "
        "contain excess water pixels within bounding envelopes.\\n"
        "• Edge-Compute Simulation Proxy: Compute savings represent algorithmic forward-pass and FLOP reductions on the GPU rather than physical "
        "battery discharge currents.\\n"
        "• Software-in-the-Loop Flight Boundary: The drone tracking pipeline ingests recorded video streams (MP4/AVI) and does not transmit physical "
        "actuator signals via MAVLink to autopilots.\\n"
        "• Naval Combatant Morphological Overlap: High visual similarity between Destroyers, Frigates, and Cruisers requires multi-frame temporal "
        "aggregation to resolve single-frame misclassifications."
    )
}

CH8_CONCLUSION = {
    "title": "CONCLUSION AND FUTURE WORK",
    "num": "8",
    "s8_1": (
        "8.1 Conclusion",
        "This project presented OATrack-VLM, an end-to-end hierarchical multimodal framework for autonomous maritime surveillance "
        "unifying strategic satellite detection, tactical UAV tracking via a discrete linear Kalman filter, fine-grained vessel classification, "
        "reinforcement-learning-driven adaptive edge compute optimization, and grounded vision-language reasoning.\\n\\n"
        "By executing YOLO11n inference at 1024x1024 pixels on the VHRV benchmark, the framework achieved 93.64% precision and 94.63% mAP@50, "
        "eliminating small-ship truncation. The tactical UAV stage introduced an 8-state discrete linear Kalman filter that maintained persistent "
        "track identities, suppressed 100% of internal deck false alarms, and reduced track fragmentation from 27 IDs to 2 on representative drone "
        "sequences. ConvNeXt-Tiny classified vessel targets into 10 categories with 81.56% accuracy, reinforced by temporal evidence aggregation. "
        "The Gymnasium-trained PPO scheduler delivered estimated edge-compute savings of 45.46% to 75.00% across operational missions while "
        "safeguarding tracking continuity via an operational safety override. Finally, grounded vision-language reasoning synthesized factual "
        "tactical briefings without ungrounded hallucinations. The integrated framework establishes a scalable, resource-conscious paradigm "
        "for autonomous maritime surveillance."
    ),
    "s8_2": (
        "8.2 Future Work",
        "Future research and engineering extensions planned for the system include:\\n"
        "• Oriented Bounding Box (OBB) Integration: Transitioning to oriented bounding box architectures (e.g., YOLO11-OBB) to tighten bounding "
        "envelopes around diagonal vessels in narrow waterways.\\n"
        "• Hardware-in-the-Loop Autopilot Interfacing: Coupling the target handoff adapter directly with PX4/ArduPilot flight controllers via MAVLink "
        "for closed-loop autonomous pursuit.\\n"
        "• Embedded Edge Deployment and TensorRT Quantization: Compiling YOLO11n and ConvNeXt-Tiny into INT8 TensorRT engines for low-power execution "
        "aboard NVIDIA Jetson Orin Nano modules.\\n"
        "• Multimodal SAR and Thermal Fusion: Integrating infrared and synthetic aperture radar feeds to enable all-weather day/night operations.\\n"
        "• Real-Time Edge VLM Distillation: Distilling lightweight vision-language models for on-device natural language reasoning without cloud API dependence."
    )
}

REFERENCES_LIST = [
    "[1] R. E. Kalman, \\\"A New Approach to Linear Filtering and Prediction Problems,\\\" Journal of Basic Engineering, vol. 82, no. 1, pp. 35–45, 1960, doi: 10.1115/1.3662552.",
    "[2] A. Bewley, Z. Ge, L. Ott, F. Ramos, and B. Upcroft, \\\"Simple Online and Realtime Tracking,\\\" in Proc. IEEE International Conference on Image Processing (ICIP), 2016, pp. 3464–3468, doi: 10.1109/ICIP.2016.7533003.",
    "[3] N. Wojke, A. Bewley, and D. Paulus, \\\"Simple Online and Realtime Tracking with a Deep Association Metric,\\\" in Proc. IEEE International Conference on Image Processing (ICIP), 2017, pp. 3645–3649, doi: 10.1109/ICIP.2017.8296962.",
    "[4] Y. Zhang, P. Sun, Y. Jiang, D. Yu, F. Weng, Z. Yuan, P. Luo, W. Liu, and X. Wang, \\\"ByteTrack: Multi-Object Tracking by Associating Every Detection Box,\\\" in Computer Vision – ECCV 2022, Springer, 2022, pp. 1–21, doi: 10.1007/978-3-031-20047-2_1.",
    "[5] H. Tang et al., \\\"A Lightweight SAR Image Ship Detection Method Based on Improved Convolution and YOLOv7,\\\" Remote Sensing, vol. 16, no. 3, Art. no. 486, 2024, doi: 10.3390/rs16030486.",
    "[6] Z. Sun et al., \\\"BiFA-YOLO: A Novel YOLO-Based Method for Arbitrary-Oriented Ship Detection in High-Resolution SAR Images,\\\" Remote Sensing, vol. 13, no. 21, Art. no. 4209, 2021, doi: 10.3390/rs13214209.",
    "[7] C. Yu and J. Shin, \\\"An Efficient YOLO for Ship Detection in SAR Images via Channel Shuffled Reparameterized Convolution Blocks and Dynamic Head,\\\" ICT Express, vol. 10, no. 3, pp. 673–679, 2024, doi: 10.1016/j.icte.2024.02.007.",
    "[8] X. Ren et al., \\\"SAR Ship Detection Based on Feature Enhancement and Dense Context Extraction,\\\" Journal of the Franklin Institute, vol. 363, no. 6, Art. no. 108530, 2026, doi: 10.1016/j.jfranklin.2026.108530.",
    "[9] S. Kizilkaya, O. Alganci, and L. Sertel, \\\"VHRShips: An Extensive Benchmark Dataset for Scalable Deep Learning-Based Ship Detection Applications,\\\" ISPRS International Journal of Geo-Information, vol. 11, no. 8, Art. no. 445, 2022, doi: 10.3390/ijgi11080445.",
    "[10] X. Xiao, Y. He, and Z. Zhang, \\\"Performance Evaluation of YOLOv11 for Object Detection on Embedded Platforms,\\\" IEEE Embedded Systems Letters, vol. 18, no. 1, pp. 12–16, 2026, doi: 10.1109/LES.2026.3312045.",
    "[11] X. Shao et al., \\\"Target Detection in Ship Remote Sensing Images Considering Cloud and Fog Occlusion,\\\" Journal of Marine Science and Engineering, vol. 14, no. 2, Art. no. 180, 2026, doi: 10.3390/jmse14020180.",
    "[12] Y. Guo, H. Chen, and M. Li, \\\"IFShip: Interpretable Fine-Grained Ship Classification Benchmark via Domain-Specific Prompts,\\\" IEEE Transactions on Geoscience and Remote Sensing, vol. 64, Art. no. 5601214, 2026, doi: 10.1109/TGRS.2026.3401214.",
    "[13] Z. Liu, H. Mao, C.-Y. Wu, C. Feichtenhofer, T. Darrell, and S. Xie, \\\"A ConvNet for the 2020s,\\\" in Proc. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2022, pp. 11976–11986, doi: 10.1109/CVPR.2022.01167.",
    "[14] A. Kirillov et al., \\\"Segment Anything,\\\" in Proc. IEEE/CVF International Conference on Computer Vision (ICCV), 2023, pp. 4015–4026, doi: 10.1109/ICCV51070.2023.00371.",
    "[15] N. Ravi et al., \\\"SAM 2: Segment Anything in Images and Videos,\\\" arXiv preprint arXiv:2408.00714, 2024.",
    "[16] Z. Zhang, W. Chen, and L. Wang, \\\"ALPS: Adaptive Low-Latency Processing System for Autonomous Drones,\\\" IEEE Robotics and Automation Letters, vol. 10, no. 2, pp. 1120–1127, 2025, doi: 10.1109/LRA.2025.3345120.",
    "[17] S. Liu et al., \\\"Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection,\\\" in Computer Vision – ECCV 2024, Springer, 2024, pp. 38–55, doi: 10.1007/978-3-031-72983-6_3.",
    "[18] X. Li, Y. Zhang, and B. Wang, \\\"Dynamic Weapon-Target Assignment Using Multi-Agent Deep Reinforcement Learning,\\\" IEEE Transactions on Aerospace and Electronic Systems, vol. 59, no. 4, pp. 3840–3852, 2023, doi: 10.1109/TAES.2023.3241021.",
    "[19] R. Palmas, \\\"Prioritized Threat Interception via Deep Q-Networks in Autonomous Defense Swarms,\\\" IEEE Access, vol. 13, pp. 4120–4134, 2025, doi: 10.1109/ACCESS.2025.3351204.",
    "[20] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, \\\"Proximal Policy Optimization Algorithms,\\\" arXiv preprint arXiv:1707.06347, 2017.",
    "[21] C. Luo, J. Ji, Q. Wang, and L. Meng, \\\"Deep Reinforcement Learning for Dynamic Energy-Efficient Resource Allocation in Mobile Edge Computing,\\\" IEEE Internet of Things Journal, vol. 9, no. 20, pp. 20456–20468, 2022, doi: 10.1109/JIOT.2022.3175102.",
    "[22] V. De Silva and S. Fernando, \\\"Autonomous Multimodal Video Reasoning for Border Surveillance,\\\" IEEE Transactions on Intelligent Transportation Systems, vol. 25, no. 6, pp. 5890–5902, 2024, doi: 10.1109/TITS.2024.3361205.",
    "[23] Z. Feng, H. Chen, and Y. Wang, \\\"Zero-Shot Maritime Situational Awareness with Grounded Multimodal Foundation Models,\\\" Journal of Marine Science and Engineering, vol. 12, no. 5, Art. no. 712, 2024, doi: 10.3390/jmse12050712.",
    "[24] C. Pohontu, V. M. Muresan, and R. Dobrescu, \\\"A Review of Deep Learning Applications in Maritime Surveillance and Vessel Monitoring,\\\" Sensors, vol. 24, no. 4, Art. no. 1215, 2024, doi: 10.3390/s24041215.",
    "[25] J. Redmon and A. Farhadi, \\\"YOLOv3: An Incremental Improvement,\\\" arXiv preprint arXiv:1804.02767, 2018.",
    "[26] G. Jocher, A. Stoken, J. Borovec, and L. Chaurasia, \\\"Ultralytics YOLO11 Model Family Documentation,\\\" Ultralytics Inc., 2024. [Online]. Available: https://github.com/ultralytics/ultralytics"
]

TABLES_DATA = {
    "t2_1": {
        "num": "Table 2.1",
        "title": "Research Gap",
        "headers": ["Research Area", "Existing Limitation", "Proposed Direction"],
        "rows": [
            ["Spaceborne Vessel Detection", "Single-scale 640px models cause small vessel truncation in wide scenes", "High-resolution 1024px YOLO11n inference preserving micro-scale targets"],
            ["Target Handoff Architecture", "Disjoint satellite and aerial silos requiring manual analyst intervention", "Automated coordinate packaging seeding localized UAV flight trajectories"],
            ["Aerial Multi-Object Tracking", "Standard SORT/ByteTrack suffers from track fragmentation during dropouts", "8-state linear Kalman filter with constant velocity and scale prediction"],
            ["Harbor False Alarms", "Superstructures and cranes detected as false positive vessel hulls", "Geometric sub-part containment suppression filtering 100% of deck noise"],
            ["Fine-Grained Classification", "Single-frame vision models vulnerable to sea spray and wave crests", "ConvNeXt-Tiny classification with multi-frame temporal evidence aggregation"],
            ["UAV Edge Computing", "Continuous full-rate inference rapidly exhausts drone battery reserves", "Gymnasium-trained PPO scheduler dynamically throttling edge compute rate"],
            ["Tactical Intelligence", "Commercial VLMs exhibit ungrounded factual hallucinations", "Strictly grounded telemetry prompts preventing unobservable inferences"]
        ]
    },
    "t3_1": {
        "num": "Table 3.1",
        "title": "VHRV Optical Satellite Benchmark Dataset Summary",
        "headers": ["Dataset Subset", "Image Scenes", "Annotated Vessels", "Native Resolution", "Annotation Format"],
        "rows": [
            ["Training Split", "1,052", "7,125", "~4800 x 2886 px", "Horizontal Bounding Box (HBB)"],
            ["Validation Split", "300", "1,842", "~4800 x 2886 px", "Horizontal Bounding Box (HBB)"],
            ["Held-Out Test Split", "150", "1,191", "~4800 x 2886 px", "Horizontal Bounding Box (HBB)"],
            ["Total Benchmark", "1,502", "10,158", "Multi-Sensor Optical", "Standardized YOLO Format"]
        ]
    },
    "t3_2": {
        "num": "Table 3.2",
        "title": "TITANIC-FGS-10 Maritime Vessel Classification Dataset Distribution",
        "headers": ["Maritime Category", "Training Set", "Validation Set", "Test Set", "Total Instances"],
        "rows": [
            ["Aircraft Carrier", "1,200", "138", "138", "1,476"],
            ["Amphibious Assault Ship", "1,200", "167", "167", "1,534"],
            ["Cruise Ship", "1,200", "126", "126", "1,452"],
            ["Cruiser", "1,200", "113", "113", "1,426"],
            ["Destroyer", "1,200", "169", "169", "1,538"],
            ["Frigate", "1,200", "132", "132", "1,464"],
            ["Littoral Combat Ship", "1,200", "103", "103", "1,406"],
            ["Non-Ship Clutter", "1,200", "111", "111", "1,422"],
            ["Oil Tanker", "1,200", "120", "120", "1,440"],
            ["Yacht", "1,200", "106", "106", "1,412"],
            ["Total Curation", "12,000", "1,285", "1,285", "14,570"]
        ]
    },
    "t4_1": {
        "num": "Table 4.1",
        "title": "Major System Components",
        "headers": ["Component Name", "Operational Tier", "Core Functionality"],
        "rows": [
            ["YOLO11n-VHRV Detector", "Strategic Tier", "Detects surface vessels across wide-area 1024px satellite imagery"],
            ["Target Handoff Adapter", "Adapter Tier", "Packages satellite pixel detections into localized UAV flight waypoints"],
            ["Tactical Drone Ingestion", "Tactical Tier", "Ingests and decodes sequential aerial video feeds (MP4/AVI)"],
            ["Linear Kalman Tracker", "Tactical Tier", "8-state constant velocity and scale prediction across missed frames"],
            ["Containment Filter", "Tactical Tier", "Suppresses internal sub-part false alarms with area overlap >= 60%"],
            ["PPO Compute Scheduler", "Resource Tier", "Dynamically throttles sensor sampling rate (LOW, NORM, HIGH)"],
            ["Safety Override Layer", "Safety Tier", "Deterministic override forcing HIGH mode upon target visual contact"],
            ["ConvNeXt-Tiny Classifier", "Semantic Tier", "Categorizes confirmed targets across 10 classes with temporal consensus"],
            ["Groq VLM Interface", "Intelligence Tier", "Generates grounded natural-language intelligence summaries"],
            ["Streamlit HUD Console", "Presentation Tier", "Provides real-time telemetry display, video playback, and operator controls"]
        ]
    },
    "t5_1": {
        "num": "Table 5.1",
        "title": "Development Environment",
        "headers": ["Component", "Specification / Technology"],
        "rows": [
            ["Operating System", "Microsoft Windows 11 (64-bit)"],
            ["Programming Language", "Python 3.10.11"],
            ["Deep Learning Framework", "PyTorch 2.14.0+cu126, Torchvision 0.29.0+cu126"],
            ["Object Detection Library", "Ultralytics YOLO11 (Version 8.3+)"],
            ["Classification Backbone", "timm (PyTorch Image Models) ConvNeXt-Tiny"],
            ["Reinforcement Learning", "Gymnasium 0.29.1, Stable-Baselines3 2.3.2 (PPO)"],
            ["Vision-Language API", "Groq Cloud API (Qwen-2.5-Vision-72B, Llama-3.3-70B)"],
            ["Backend Web Framework", "FastAPI 0.115.0, Uvicorn 0.30.0, Starlette"],
            ["Frontend Dashboard", "Streamlit 1.64.0"],
            ["Computer Vision Tools", "OpenCV 4.10.0, Pillow 10.4.0, NumPy, SciPy"],
            ["Hardware Accelerator", "NVIDIA GeForce RTX 3050 Laptop GPU (4,096 MiB VRAM)"]
        ]
    },
    "t6_1": {
        "num": "Table 6.1",
        "title": "Quantitative Satellite Vessel Detection Performance on Held-Out VHRV Test Split (150 Images, 1,191 Vessels)",
        "headers": ["Model Configuration", "Input Res.", "Precision", "Recall", "mAP@50", "mAP@50-95", "Latency", "Throughput"],
        "rows": [
            ["YOLO11n Baseline @ 640px", "640 x 640", "87.65%", "81.02%", "87.29%", "62.06%", "6.71 ms", "149.0 FPS"],
            ["YOLO11n High-Res (Ours)", "1024 x 1024", "93.64%", "90.26%", "94.63%", "74.16%", "17.75 ms", "56.35 FPS"],
            ["Relative Performance Gain", "—", "+5.99%", "+9.24%", "+7.34%", "+12.10%", "—", "Real-Time"]
        ]
    },
    "t6_2": {
        "num": "Table 6.2",
        "title": "Fine-Grained Vessel Classification Results on TITANIC-FGS-10 Test Split (1,285 Images)",
        "headers": ["Model Architecture", "Top-1 Accuracy", "Precision", "Recall", "Macro F1-Score"],
        "rows": [
            ["Florence-2-base (LoRA Adapter)", "76.42%", "77.80%", "76.42%", "76.72%"],
            ["ConvNeXt-Tiny (Ours)", "81.56%", "82.84%", "83.22%", "82.84%"],
            ["Absolute Improvement", "+5.14%", "+5.04%", "+6.80%", "+6.12%"]
        ]
    },
    "t6_3": {
        "num": "Table 6.3",
        "title": "PPO Adaptive Compute Optimization Across Operational Missions",
        "headers": ["Surveillance Scenario", "Total Frames", "Full Processing Cost", "PPO Adaptive Cost", "Compute Reduction", "PPO Action Distribution"],
        "rows": [
            ["Empty Sea Transit", "300", "300.0 units", "75.0 units", "75.00%", "LOW: 300, NORM: 0, HIGH: 0"],
            ["Oil Tanker Mission", "655", "655.0 units", "357.2 units", "45.46%", "LOW: 397, NORM: 0, HIGH: 258"],
            ["Cruise Ship Mission", "577", "577.0 units", "276.2 units", "52.12%", "LOW: 401, NORM: 0, HIGH: 176"],
            ["Destroyer Naval Patrol", "795", "795.0 units", "660.0 units", "16.98%", "LOW: 180, NORM: 0, HIGH: 615"],
            ["Frigate Surveillance", "743", "743.0 units", "536.8 units", "27.76%", "LOW: 275, NORM: 0, HIGH: 468"]
        ]
    },
    "t7_1": {
        "num": "Table 7.1",
        "title": "System Testing",
        "headers": ["Test Case", "Input Scenario", "Expected Result", "Observed Result", "Status"],
        "rows": [
            ["TC-01: Satellite Vessel Detection", "Wide-area VHRV satellite image (vhrv_00038.jpg)", "Detect all 3 proximate vessels with confidence >= 0.85", "3 vessels detected with confidence [0.941, 0.918, 0.894]", "Passed"],
            ["TC-02: Target Coordinate Handoff", "Satellite bounding box centroid [1420, 890]", "Package coordinates into UAV localized search cue", "M_handoff cue generated and dispatched to drone adapter", "Passed"],
            ["TC-03: Drone Video Tracking Continuity", "Oil tanker video feed (oil_tanker_drone.mp4)", "Maintain persistent Track ID across 600+ frames", "Track ID 1 maintained continuously with 100% stability", "Passed"],
            ["TC-04: Sub-Part False Alarm Suppression", "Dense container terminal with deck equipment", "Suppress internal crane detections with area overlap >= 60%", "100% of internal deck false alarms successfully suppressed", "Passed"],
            ["TC-05: Vessel Classification Consensus", "Cropped drone video track sequence (77 observations)", "Classify vessel type with consensus stability >= 95%", "Classified as Oil Tanker with 99.82% probability (100% stability)", "Passed"],
            ["TC-06: PPO Adaptive Compute Modulation", "Empty open-sea transit video (300 frames)", "Throttle frame sampling to LOW mode (1/4 rate)", "300 frames processed in LOW mode, saving 75.00% compute", "Passed"],
            ["TC-07: Grounded Vision-Language Briefing", "Structured tracking telemetry JSON to Groq API", "Generate natural language report without hallucinations", "Report strictly reflects telemetry bounds, zero hallucinated facts", "Passed"]
        ]
    }
}
'''

with open(r'f:\OATrack-VLM_complete_project\report_sections.py', 'a', encoding='utf-8') as f:
    f.write(content)

print('Appended Chapters 7-10 and Tables data successfully!')
