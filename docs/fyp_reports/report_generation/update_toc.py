# Update TOC, LOT, and LOF numbers in optimize_report_layout.py by line replacement
with open(r'f:\OATrack-VLM_complete_project\optimize_report_layout.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_toc_p1 = """toc_p1 = [
    ("", "Abstract", "IV"),
    ("", "List of Tables", "X"),
    ("", "List of Figures", "XI"),
    ("", "List of Abbreviations", "XII"),
    ("1", "INTRODUCTION", "1"),
    ("1.1", "Background of Maritime Domain Awareness & Aerial Surveillance", "2"),
    ("1.2", "Problem Statement", "2"),
    ("1.3", "Motivation", "3"),
    ("1.4", "Objective", "3"),
    ("1.5", "Scope of the Project", "4"),
    ("1.6", "Existing System and Limitations", "4"),
    ("1.7", "Proposed Solution", "5"),
    ("2", "LITERATURE REVIEW", "6"),
    ("2.1", "Satellite Remote Sensing for Vessel Detection", "6"),
    ("2.2", "Multi-Object Tracking and Kalman Filtering in Aerial Feeds", "6"),
    ("2.3", "Fine-Grained Maritime Vessel Classification", "7"),
    ("2.4", "Adaptive Edge Computing and Reinforcement Learning", "7"),
    ("2.5", "Vision-Language Models in Tactical Surveillance", "7"),
    ("2.6", "Research Gap", "8"),
    ("2.7", "Contribution of the Proposed Work", "9")
]
"""

new_toc_p2 = """toc_p2 = [
    ("3", "DATASET AND PROPOSED METHODOLOGY", "10"),
    ("3.1", "VHRV Optical Satellite Benchmark Dataset", "10"),
    ("3.2", "TITANIC-FGS-10 Maritime Classification Dataset", "10"),
    ("3.3", "Data Preprocessing and Ground-Truth Integrity Verification", "11"),
    ("3.4", "Strategic Satellite-Based Vessel Detection (YOLO11n @ 1024px)", "11"),
    ("3.5", "Target Handoff Adapter Architecture", "11"),
    ("3.6", "Tactical UAV Tracking via Discrete Linear Kalman Filter", "12"),
    ("3.6.1", "8-State Dynamical State Formulation", "12"),
    ("3.6.2", "Multi-Feature Data Association Metric", "12"),
    ("3.6.3", "Sub-Part Containment Suppression Filter", "13"),
    ("3.7", "Fine-Grained Classification & Evidence Aggregation", "13"),
    ("3.8", "PPO Adaptive Edge Compute Scheduling", "13"),
    ("3.9", "Grounded Vision-Language Reasoning Architecture", "14"),
    ("4", "SYSTEM DESIGN AND ARCHITECTURE", "15"),
    ("4.1", "Overall System Architecture", "15"),
    ("4.2", "Data Flow Pipeline", "16"),
    ("4.3", "Surveillance Processing Workflow", "16"),
    ("4.4", "Proposed Application Architecture", "16"),
    ("4.5", "System Components", "17")
]
"""

new_toc_p3 = """toc_p3 = [
    ("5", "METHODOLOGY", "18"),
    ("5.1", "Development Environment", "18"),
    ("5.2", "Model Implementation Details", "18"),
    ("5.3", "Baseline Models", "19"),
    ("5.4", "OATrack-VLM Implementation Workflow", "19"),
    ("5.5", "Streamlit Command Center Prototype", "19"),
    ("5.6", "Prototype Operational Workflow", "20"),
    ("6", "RESULTS AND ANALYSIS", "21"),
    ("6.1", "Experimental Setup", "21"),
    ("6.2", "Evaluation Metrics", "21"),
    ("6.3", "Satellite Vessel Detection Results", "21"),
    ("6.4", "UAV Tracking and Motion Persistence Performance", "22"),
    ("6.5", "Fine-Grained Classification Results", "23"),
    ("6.6", "Training and Convergence Analysis", "24"),
    ("6.7", "PPO Adaptive Compute Optimization Across Scenarios", "25"),
    ("6.8", "Multi-Ship Anchorage and Dense Harbor Analysis", "26"),
    ("6.9", "Grounded Vision-Language Telemetry Briefings", "26"),
    ("6.10", "Discussion", "26"),
    ("7", "EXPERIMENTAL RESULTS", "27"),
    ("7.1", "System Testing", "27"),
    ("7.2", "Current Achievements", "27"),
    ("7.3", "Limitations", "28")
]
"""

new_toc_p4 = """toc_p4 = [
    ("8", "CONCLUSION AND FUTURE WORK", "29"),
    ("8.1", "Conclusion", "29"),
    ("8.2", "Future Work", "29"),
    ("9", "REFERENCES", "31"),
    ("10", "APPENDICES", "33"),
    ("10.1", "Sample Inputs and Outputs", "33"),
    ("10.2", "Additional Diagnostic Visualizations and Loss Curves", "33"),
    ("10.3", "Project Execution Gantt Chart", "34"),
    ("10.4", "Plagiarism Verification Report", "35"),
    ("10.5", "Academic Paper Publication Details", "36")
]
"""

new_lot = """lot_rows = [
    ("2.1", "Research Gap", "8"),
    ("3.1", "VHRV Optical Satellite Benchmark Dataset Summary", "10"),
    ("3.2", "TITANIC-FGS-10 Maritime Vessel Classification Dataset Distribution", "12"),
    ("4.1", "Major System Components", "17"),
    ("5.1", "Development Environment", "18"),
    ("6.1", "Quantitative Satellite Vessel Detection Performance on VHRV Test Split", "22"),
    ("6.2", "Fine-Grained Vessel Classification Results on TITANIC-FGS-10 Test Split", "24"),
    ("6.3", "PPO Adaptive Compute Optimization Across Operational Missions", "25"),
    ("7.1", "System Testing", "27")
]
"""

new_lof = """lof_rows = [
    ("3.1", "Dataset Preparation and Construction Pipeline for VHRV Benchmark", "11"),
    ("3.2", "Discrete Linear Kalman Filter Tracking Pipeline and State Transitions", "13"),
    ("4.1", "End-to-End Hierarchical System Architecture of OATrack-VLM Framework", "16"),
    ("5.1", "Maritime Surveillance Command Center Operations Dashboard (Streamlit)", "20"),
    ("6.1", "High-Resolution Satellite Vessel Detection Localization on VHRV Test Split", "22"),
    ("6.2", "Tactical UAV Persistent Tracking Visualization with Motion Trail", "23"),
    ("6.3", "Normalized Confusion Matrix of ConvNeXt-Tiny on TITANIC-FGS-10", "24"),
    ("6.4", "Model Training and Validation Convergence Curves", "25"),
    ("6.5", "Estimated Edge-Compute Savings Breakdown Across Maritime Scenarios", "26"),
    ("10.1", "Sample Satellite Detection Output and Grounded Groq VLM Intelligence Briefing", "33"),
    ("10.2", "Tactical UAV Video Frame Telemetry and Consensus Classification Output", "33"),
    ("10.3", "Detailed Detector Training and Validation Loss Progression Curves", "33"),
    ("10.4", "Project Execution Gantt Chart Across Academic Timeline", "34")
]
"""

content = "".join(lines)

def replace_block(text, start_marker, end_marker, replacement):
    idx_start = text.find(start_marker)
    if idx_start == -1:
        raise ValueError(f"Marker not found: {start_marker}")
    idx_end = text.find(end_marker, idx_start)
    if idx_end == -1:
        raise ValueError(f"Marker not found: {end_marker}")
    idx_end += len(end_marker)
    return text[:idx_start] + replacement + text[idx_end:]

content = replace_block(content, "toc_p1 = [", "add_toc_rows(t1, toc_p1)", new_toc_p1 + "add_toc_rows(t1, toc_p1)")
content = replace_block(content, "toc_p2 = [", "add_toc_rows(t2, toc_p2)", new_toc_p2 + "add_toc_rows(t2, toc_p2)")
content = replace_block(content, "toc_p3 = [", "add_toc_rows(t3, toc_p3)", new_toc_p3 + "add_toc_rows(t3, toc_p3)")
content = replace_block(content, "toc_p4 = [", "add_toc_rows(t4, toc_p4)", new_toc_p4 + "add_toc_rows(t4, toc_p4)")
content = replace_block(content, "lot_rows = [", "add_toc_rows(t_lot, lot_rows)", new_lot + "add_toc_rows(t_lot, lot_rows)")
content = replace_block(content, "lof_rows = [", "add_toc_rows(t_lof, lof_rows)", new_lof + "add_toc_rows(t_lof, lof_rows)")

with open(r'f:\OATrack-VLM_complete_project\optimize_report_layout.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: optimize_report_layout.py updated successfully!")
