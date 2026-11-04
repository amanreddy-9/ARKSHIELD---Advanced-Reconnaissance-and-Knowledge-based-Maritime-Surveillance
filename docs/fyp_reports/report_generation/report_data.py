# report_data.py - Structured Content for OATrack-VLM Project Report

TITLE = "OATRACK-VLM: A HIERARCHICAL MULTIMODAL FRAMEWORK FOR AUTONOMOUS MARITIME SURVEILLANCE USING SATELLITE DETECTION, KALMAN-FILTER UAV TRACKING, AND VISION-LANGUAGE REASONING"

STUDENTS = [
    ("AMAN REDDY J", "CH.SC.U4AIE23006"),
    ("BTPR NIKHIL", "CH.SC.U4AIE23005")
]

SUPERVISOR = {
    "name": "Dr. K ASHWINI",
    "designation": "Assistant Professor (Sr. Gr.)",
    "dept": "Department of Computer Science and Engineering",
    "school": "Amrita School of Computing",
    "campus": "Chennai – 601103"
}

CHAIRPERSON = {
    "name": "DR. S. BAGHAVATHI PRIYA",
    "designation": "Associate Professor Dept. of CSE.",
    "role": "CHAIRPERSON"
}

PROGRAM_CHAIR = "Dr. S. Natarajan"
PRINCIPAL = "Dr. V. Jayakumar"
CAMPUS_DIRECTOR = "Mr. I B Manikantan"
ADMIN_DIRECTOR = "Swami Vinayamritananda Puri"
CHANCELLOR = "Sri Mata Amritanandamayi Devi"

SUBMISSION_DATE = "October 2026"

KEYWORDS = "Maritime Surveillance, Satellite Detection, UAV Tracking, Kalman Filter, Vessel Classification, Adaptive Edge Computing, Reinforcement Learning, Vision-Language Models."

ABSTRACT_TEXT = (
    "Persistent maritime domain awareness requires bridging strategic wide-area observation with "
    "tactical localized inspection under severe edge-compute and bandwidth constraints. This project presents "
    "OATrack-VLM, an end-to-end hierarchical multimodal framework that unifies high-resolution optical satellite "
    "vessel detection, tactical unmanned aerial vehicle (UAV) tracking via an 8-state discrete linear Kalman filter, "
    "fine-grained maritime vessel classification, reinforcement-learning-driven adaptive edge-compute scheduling, "
    "and grounded vision-language reasoning.\n\n"
    "Strategic wide-area surveillance employs a fine-tuned YOLO11n object detector operating at high input "
    "resolution (1024×1024 pixels) on the VHRV optical satellite benchmark (1,502 scenes, 10,158 authentic vessels), "
    "achieving 93.64% precision, 90.26% recall, 94.63% mAP@50, and 74.16% mAP@50-95, overcoming downsampling "
    "truncation of small craft. Target coordinates and bounding geometries are autonomously packaged by a handoff "
    "adapter to seed localized UAV inspection routes, eliminating wasteful open-ocean transit search patterns. "
    "In the tactical UAV stage, an 8-state discrete linear Kalman filter coupled with multi-feature data association "
    "(incorporating bounding box IoU, normalized centroid displacement, aspect-ratio similarity, and motion heading) "
    "and sub-part containment suppression maintains persistent vessel identities across temporary detector dropouts, "
    "reducing track fragmentation from 27 IDs to 2 on representative drone video sequences while suppressing 100% of "
    "internal deck false alarms.\n\n"
    "Target vessel crops are categorized across ten fine-grained maritime classes using ConvNeXt-Tiny trained on "
    "the TITANIC-FGS-10 dataset (14,570 images), achieving 81.56% top-1 accuracy and 82.84% macro F1-score, reinforced "
    "by multi-frame temporal evidence aggregation. To extend UAV flight endurance, an integrated Gymnasium-trained "
    "Proximal Policy Optimization (PPO) agent dynamically modulates sensor inference frequency between lightweight, "
    "standard, and high-rate modes, achieving estimated edge-compute reductions of 75.00% on empty open sea and "
    "45.46% to 52.12% during active naval missions, while an operational safety override deterministically guarantees "
    "tracking continuity. Finally, a grounded vision-language reasoning layer synthesizes telemetry-verified tactical "
    "briefings without hallucinations. The complete system is demonstrated via a high-performance FastAPI backend "
    "and a Streamlit maritime surveillance operations console."
)

ACKNOWLEDGEMENT_TEXT = (
    "This project work would not have been possible without the contribution and support of many people. "
    "It gives us immense pleasure to express our profound gratitude to our honorable Chancellor, "
    "Sri Mata Amritanandamayi Devi, for her divine blessings and for being a constant source of inspiration.\n\n"
    "We are indebted to extend our sincere gratitude to our Administrative Director, Swami Vinayamritananda Puri, "
    "and Campus Director, Mr. I B Manikantan, Amrita School of Computing, Amrita Vishwa Vidyapeetham, Chennai Campus, "
    "for facilitating all the infrastructural facilities and providing an extended environment to gain valuable education "
    "and research experience.\n\n"
    "We register our special thanks to Dr. V. Jayakumar, Principal, Amrita School of Computing, for the institutional support "
    "extended to us in the successful conduct of this project. We wish to express our heartfelt gratitude to Dr. S. Baghavathi Priya, "
    "Chairperson, Department of Computer Science and Engineering, Dr. S. Natarajan, Program Chair, and to our project supervisor, "
    "Dr. K Ashwini, Assistant Professor (Sr. Gr.), Department of Computer Science and Engineering, for their inspiring guidance, "
    "technical insights, personal involvement, and constant encouragement throughout the entire course of this project work.\n\n"
    "We are sincerely grateful to the Project Coordinators, Review Panel Members, and the entire faculty of the Department of "
    "Computer Science and Engineering for their constructive critiques, critical evaluation, and valuable recommendations, "
    "which served as a rich source to enhance the scientific rigor and overall quality of this work."
)

ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"),
    ("UAV", "Unmanned Aerial Vehicle"),
    ("VLM", "Vision-Language Model"),
    ("SAR", "Synthetic Aperture Radar"),
    ("EEZ", "Exclusive Economic Zone"),
    ("HBB", "Horizontal Bounding Box"),
    ("OBB", "Oriented Bounding Box"),
    ("MOT", "Multi-Object Tracking"),
    ("SORT", "Simple Online and Realtime Tracking"),
    ("IoU", "Intersection over Union"),
    ("mAP", "Mean Average Precision"),
    ("PPO", "Proximal Policy Optimization"),
    ("DRL", "Deep Reinforcement Learning"),
    ("HUD", "Heads-Up Display"),
    ("SGD", "Stochastic Gradient Descent"),
    ("VHRV", "Very-High-Resolution Vessel Dataset"),
    ("TITANIC-FGS", "Fine-Grained Ship Classification Dataset"),
    ("API", "Application Programming Interface"),
    ("GPU", "Graphics Processing Unit"),
    ("CSV", "Comma-Separated Values"),
    ("JSON", "JavaScript Object Notation"),
    ("REST", "Representational State Transfer"),
    ("TP", "True Positive"),
    ("TN", "True Negative"),
    ("FP", "False Positive"),
    ("FN", "False Negative")
]
