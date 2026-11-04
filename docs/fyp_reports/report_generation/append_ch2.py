import os

ch2_text = '''
CH2_LIT = {
    "title": "LITERATURE REVIEW",
    "num": "2",
    "intro": (
        "Automated maritime surveillance has witnessed substantial technological evolution driven by deep learning, "
        "high-resolution spaceborne remote sensing, multi-object tracking (MOT) algorithms, edge computing, and large "
        "multimodal models. Early maritime monitoring systems relied heavily on manual radar plotting, handcrafted feature "
        "extractors (e.g., Haar cascades, HOG), and basic constant-velocity kinematics. While foundational, these early techniques "
        "failed to generalize across complex oceanic clutter, sea spray, variable solar illumination, and dense vessel anchorages. "
        "This chapter reviews recent academic advancements across five core pillars: spaceborne vessel detection, multi-object "
        "aerial tracking, fine-grained vessel categorization, reinforcement-learning-driven edge computing, and vision-language "
        "intelligence synthesis, identifying critical research gaps addressed by OATrack-VLM."
    ),
    "s2_1": (
        "2.1 Satellite Remote Sensing for Vessel Detection",
        "Recent advances in convolutional neural networks (CNNs) have substantially elevated target detection benchmarks from "
        "optical and Synthetic Aperture Radar (SAR) remote sensing platforms. Tang et al. [5] engineered a lightweight SAR vessel "
        "detection architecture based on an enhanced YOLOv7 network with specialized convolutions to suppress speckle noise. "
        "Sun et al. [6] introduced BiFA-YOLO, utilizing bidirectional feature alignment to detect arbitrary-oriented vessels in SAR images. "
        "Yu and Shin [7] proposed an efficient YOLO variant for SAR imagery using channel-shuffled reparameterized convolution blocks and dynamic "
        "detection heads. Ren et al. [8] tackled dense harbor environments using dense context extraction and multi-scale feature enhancement. "
        "In the optical domain, Kizilkaya et al. [9] developed the VHRShips benchmark to standardize evaluation on very-high-resolution optical "
        "satellite imagery, demonstrating that standard models struggle on micro-scale vessels. Xiao et al. [10] verified that YOLOv11n delivers "
        "superior inference latency on embedded GPU accelerators. However, these prior studies focus exclusively on static single-frame "
        "localization and fail to address target handoff to dynamic aerial robotic platforms."
    ),
    "s2_2": (
        "2.2 Multi-Object Tracking and Kalman Filtering in Dynamic Aerial Feeds",
        "Multi-object tracking in continuous aerial feeds predominantly adopts the tracking-by-detection framework. The pioneering "
        "Simple Online and Realtime Tracking (SORT) algorithm by Bewley et al. [2] coupled an 8-state linear Kalman filter [1] with the "
        "Hungarian matching algorithm, establishing high frame-rate tracking for bounding boxes with high temporal overlap. Wojke et al. [3] "
        "introduced DeepSORT, incorporating deep visual appearance embeddings to re-identify tracks across long occlusions, though at "
        "substantial GPU inference overhead. Zhang et al. [4] developed ByteTrack, a two-stage association pipeline that matches high-confidence "
        "detections first and pairs low-confidence detections with active tracks to recover occluded targets.\\n\\n"
        "While effective for terrestrial street surveillance, applying standard MOT algorithms to maritime drone footage encounters severe "
        "domain barriers: vessel bounding boxes scale dramatically with UAV altitude changes, high-speed wake turbulence generates false positives, "
        "and adjacent moored vessels frequently merge into single tracks. Furthermore, brief detector dropouts cause standard trackers to drop "
        "tracks prematurely, resulting in excessive ID switching. This project addresses these challenges through an 8-state discrete linear "
        "Kalman filter with a multi-feature affinity cost and sub-part containment suppression."
    ),
    "s2_3": (
        "2.3 Fine-Grained Maritime Vessel Classification",
        "Fine-grained vessel recognition presents severe computer vision challenges due to high intra-class variation (variable vessel paint schemes, "
        "deck cargo loading, crane deployments) and low inter-class variation among specialized naval combatants (such as Frigates, Destroyers, "
        "and Cruisers) [12]. Liu et al. [13] introduced ConvNeXt, re-engineering standard convolutional networks with inverted bottlenecks and "
        "large 7x7 kernels to match Vision Transformer (ViT) accuracy with substantially lower computational complexity. Guo et al. [12] "
        "developed IFShip and curated the TITANIC-FGS benchmark, exploring domain-specific prompt engineering and multimodal classifiers. "
        "While large foundation vision models (e.g., SAM [14], SAM 2 [15], Grounding DINO [17]) exhibit remarkable open-world segmentation, "
        "their multi-gigabyte memory footprints and high latency exceed the payload constraints of tactical UAVs. In this project, ConvNeXt-Tiny "
        "serves as an efficient edge classifier, stabilized by multi-frame temporal evidence aggregation."
    ),
    "s2_4": (
        "2.4 Adaptive Edge Computing and Reinforcement Learning",
        "Deploying deep vision models aboard battery-constrained UAVs requires balancing detection accuracy against electrical power draw. "
        "Li et al. [18] and Palmas [19] investigated deep reinforcement learning (DRL) for tactical drone trajectory planning and defense prioritization. "
        "Schulman et al. [20] formulated Proximal Policy Optimization (PPO), which offers stable, sample-efficient on-policy reinforcement "
        "learning across continuous state spaces and discrete action sets. Luo et al. [21] examined reinforcement learning for edge resource "
        "allocation in wireless sensor networks. In this project, PPO is leveraged to dynamically modulate UAV vision inference frequency "
        "based on scene complexity, target presence, and tracking continuity, coupled with a deterministic safety override."
    ),
    "s2_5": (
        "2.5 Vision-Language Models in Tactical Surveillance",
        "Recent breakthroughs in multimodal Large Language Models (VLMs) have enabled automated video reasoning and situational report generation "
        "[22, 23]. However, commercial, unconstrained VLMs frequently hallucinate tactical attributes (e.g., fabricated hull registration numbers, "
        "vessel nationalities, or unobservable weaponry). In this work, vision-language reasoning is grounded by passing verified bounding boxes, "
        "persistent track IDs, and classifier softmax probabilities directly within structured telemetry prompts to Groq-hosted models, "
        "enforcing strict operational verifiability."
    ),
    "s2_6": (
        "2.6 Research Gap",
        "Despite significant progress across individual domains, several critical technical gaps persist in existing literature, as "
        "summarized in Table 2.1:\\n"
        "1. Lack of unified end-to-end integration connecting strategic wide-area satellite detection with tactical aerial drone tracking.\\n"
        "2. High track fragmentation and identity switching in aerial maritime feeds under temporary detector dropouts.\\n"
        "3. Inability of standard detectors to filter internal sub-part false alarms (e.g., container cranes or deck superstructures).\\n"
        "4. Absence of dynamic, scene-adaptive compute scheduling to conserve UAV battery life during quiescent ocean patrols.\\n"
        "5. Susceptibility of vision-language surveillance models to ungrounded factual hallucinations."
    ),
    "s2_7": (
        "2.7 Contribution of the Proposed Work",
        "The OATrack-VLM framework addresses these gaps through five primary technical contributions:\\n"
        "1. Strategic High-Resolution Satellite Detection: A fine-tuned YOLO11n model operating at 1024x1024 pixels on the VHRV benchmark "
        "achieves 93.64% precision and 94.63% mAP@50, eliminating spatial downsampling truncation of small craft.\\n"
        "2. Autonomous Target Handoff Adapter: Translates satellite detections into tactical UAV mission coordinates, eliminating blind searching.\\n"
        "3. Robust Kalman Filter Tracking & Containment Suppression: An 8-state discrete linear Kalman filter with multi-feature affinity costing "
        "and sub-part containment suppression reduces track fragmentation from 27 IDs to 2 on representative drone videos.\\n"
        "4. Stable Fine-Grained Classification: ConvNeXt-Tiny achieves 81.56% top-1 accuracy on TITANIC-FGS-10, stabilized by temporal evidence aggregation.\\n"
        "5. PPO Adaptive Compute Optimization: Delivers 75% compute savings on empty water and 45.46% to 52.12% during active missions with safety overrides.\\n"
        "6. Grounded VLM Telemetry Briefings: Generates hallucination-free tactical intelligence summaries via Groq-hosted vision-language models."
    )
}
'''

with open(r'f:\OATrack-VLM_complete_project\report_sections.py', 'a', encoding='utf-8') as f:
    f.write(ch2_text)

print('Appended Chapter 2 successfully!')
