# Overleaf Compilation Instructions for OATrack-VLM IEEE Paper

This directory contains the complete, publication-ready IEEE conference paper for **OATrack-VLM: A Hierarchical Multimodal Framework for Autonomous Maritime Surveillance**.

---

## 📁 Directory Structure

```
paper/
├── main.tex                    # Master IEEEtran LaTeX document
├── references.bib              # Verified BibTeX bibliography
├── README.md                   # This instruction guide
└── figures/                    # Publication figures (300 DPI PNGs)
    ├── system_architecture.png
    ├── kalman_tracking_pipeline.png
    ├── satellite_detection.png
    ├── uav_tracking.png
    ├── confusion_matrix.png
    ├── training_curves.png
    └── adaptive_compute_breakdown.png
```

---

## 🚀 How to Upload & Compile on Overleaf

1. **Compress the Paper Directory**:
   Select the `paper/` folder (or all contents inside: `main.tex`, `references.bib`, and the `figures/` folder) and compress them into a `.zip` archive:
   - On Windows: Right-click `paper` $\rightarrow$ **Send to** $\rightarrow$ **Compressed (zipped) folder** (e.g., `OATrack_VLM_Paper.zip`).
   
2. **Import to Overleaf**:
   - Log into [Overleaf](https://www.overleaf.com/).
   - Click **New Project** $\rightarrow$ **Upload Project**.
   - Drag and drop `OATrack_VLM_Paper.zip`.

3. **Compile Settings**:
   - Ensure the compiler is set to **pdfLaTeX** (default in Overleaf).
   - Set the Main document to `main.tex`.
   - Click **Recompile**.

---

## 🛠️ Local Compilation (TeX Live / MiKTeX)

If compiling locally on Windows, Linux, or macOS:

```bash
cd paper
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Output PDF will be generated as `main.pdf`.

---

## 📊 Summary of Verified Results in the Paper

- **Satellite Detector (YOLO11n @ 1024px)**:
  - Benchmark: VHRV Optical Satellite Test Split (150 images, 1,191 vessels)
  - Precision: **93.64%**, Recall: **90.26%**, mAP@50: **94.63%**, mAP@50-95: **74.16%**
  - Inference Latency: **17.75 ms** (56.35 FPS)

- **Kalman Filter UAV Tracking**:
  - State: 8D Constant Velocity $[c_x, c_y, w, h, v_x, v_y, v_w, v_h]^T$
  - Multi-feature data association + sub-part containment suppression
  - Coasting persistence up to 45 missed frames; reduced track fragmentation from 27 IDs to 2 on representative drone video.

- **Vessel Classifier (ConvNeXt-Tiny)**:
  - Benchmark: TITANIC-FGS-10 Test Split (1,285 images across 10 classes)
  - Overall Accuracy: **81.56%**, Macro F1: **82.84%**

- **PPO Adaptive Compute Scheduler**:
  - Empty Sea: **75.00%** compute reduction
  - Oil Tanker Mission: **45.46%** compute reduction
  - Cruise Ship Mission: **52.12%** compute reduction
  - Operational safety override guarantees zero missed target handoffs.
