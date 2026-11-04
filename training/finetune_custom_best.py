"""
training/finetune_custom_best.py
Fine-tunes the baseline vhrv_best.pt checkpoint on VHRV satellite imagery with:
- Warm start from converged vhrv_best.pt weights (preserves high-precision feature extractors)
- Gentle learning rate (lr0=0.0003, lrf=0.1) for fine-grained domain refinement
- Spatial maritime augmentations: flipud=0.5, fliplr=0.5, degrees=10.0
- Batch=4, mixed precision (AMP) for RTX 3050 Laptop GPU
- Saves improved weights to models/weights/vhrv_custom_best.pt
"""
import shutil
from pathlib import Path
from ultralytics import YOLO

def main():
    base_weights = "models/weights/vhrv_best.pt"
    data_yaml = "data/vhrv/vhrv/vhrv.yaml"
    project = "runs/detect"
    name = "vhrv_custom_enhanced"

    print("=" * 65)
    print("ENHANCING CUSTOM MARITIME YOLO DETECTOR (FINE-TUNING FROM BASELINE)")
    print(f"Base Weights: {base_weights}")
    print(f"Data YAML:    {data_yaml}")
    print("=" * 65)

    model = YOLO(base_weights)

    results = model.train(
        data=data_yaml,
        epochs=3,
        imgsz=1024,
        batch=4,
        device=0,
        workers=0,
        amp=True,
        lr0=0.0003,
        lrf=0.1,
        weight_decay=0.0005,
        flipud=0.5,
        fliplr=0.5,
        degrees=10.0,
        scale=0.2,
        mosaic=0.3,
        close_mosaic=1,
        project=project,
        name=name,
        exist_ok=True,
        verbose=True,
        save=True,
    )

    trained_best = Path(project) / name / "weights" / "best.pt"
    trained_last = Path(project) / name / "weights" / "last.pt"
    target_path = Path("models/weights/vhrv_custom_best.pt")

    chosen = trained_best if trained_best.exists() else trained_last
    if chosen.exists():
        shutil.copy2(str(chosen), str(target_path))
        print(f"\n[SUCCESS] Updated {target_path} from {chosen}")
    else:
        print("[WARN] Could not find trained checkpoint weights.")

if __name__ == "__main__":
    main()
