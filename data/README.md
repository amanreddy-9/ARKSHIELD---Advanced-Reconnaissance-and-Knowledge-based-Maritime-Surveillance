# ARKSHIELD Dataset Setup Guide

This directory holds the training and evaluation datasets for the ARKSHIELD maritime surveillance system.

Due to file size constraints (~7.3 GB total), datasets are excluded from version control and downloaded separately.

---

## 1. Directory Structure

Ensure your `data/` folder is structured as follows:

```
data/
├── vhrv/
│   └── vhrv/
│       ├── vhrv.yaml
│       ├── images/
│       │   ├── train/     # 1,052 high-resolution satellite optical images
│       │   ├── val/       # 300 validation images
│       │   └── test/      # 150 test images (~4800x2886 resolution)
│       └── labels/
│           ├── train/     # YOLO format bounding box annotations (class 0: vessel)
│           ├── val/
│           └── test/
│
├── TITANIC-FGS-10/
│   ├── ImageNet/
│   │   ├── train/         # 12,000 images across 10 fine-grained vessel classes
│   │   ├── val/           # 1,285 images
│   │   └── test/          # 1,285 images
│   └── Instruction_train/
│       └── ship_data_10class.json
│
├── test_mp4/
│   ├── test1.mp4                   # Naval Frigate KD Kasturi F25 patrol feed (30 FPS)
│   ├── oil_tanker_drone.mp4        # Commercial oil tanker open sea surveillance
│   ├── cruise_ship_drone.mp4       # Cruise ship surveillance footage
│   └── aircraft_carrier_drone.mp4  # Aircraft carrier flight deck footage
│
└── results/                        # Output folder for annotated videos and detection overlays
```

---

## 2. Dataset Descriptions

### A. VHRV (Very High Resolution Vessel Dataset)
- **Modality**: Optical Satellite Imagery (HBB)
- **Image Size**: ~4,800 × 2,886 pixels native
- **Target Class**: Single class (`vessel`)
- **Usage**: Used for high-resolution (`imgsz=1024`) detector fine-tuning in `training/train_vhrv.py` and evaluation in `training/evaluate_detector.py`.

### B. TITANIC-FGS-10 Dataset
- **Modality**: Optical vessel crops for fine-grained classification
- **Classes (10)**:
  1. `Aircraft_carrier`
  2. `Amphibious_assault_ship`
  3. `Cruise_ship`
  4. `Cruiser`
  5. `Destroyer`
  6. `Frigate`
  7. `Littoral_combat_ship`
  8. `Non_ship`
  9. `Oil_tanker`
  10. `Yacht`
- **Usage**: Used to train the ConvNeXt-Tiny classifier in `training/train_convnext_tiny.py`.

### C. Tactical Drone Test Footage (`test_mp4/`)
- Accepts standard drone surveillance formats: `.mp4`, `.avi`, `.mov`.
- Output videos annotated with 8-state continuous Kalman bounding boxes, trajectory trails, and smoothed classifier predictions are saved to `data/results/`.
