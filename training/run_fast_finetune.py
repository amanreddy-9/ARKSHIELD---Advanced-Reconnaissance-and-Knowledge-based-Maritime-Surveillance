"""
training/run_fast_finetune.py
Fine-tunes vhrv_best.pt on curated high-resolution maritime satellite images.
Preserves converged spatial features while refining maritime orientation and small-vessel anchors.
"""
from pathlib import Path
import shutil
from ultralytics import YOLO

def main():
    base_model = "models/weights/vhrv_best.pt"
    data_yaml = "configs/vhrv_finetune.yaml"
    project = "runs/detect"
    name = "vhrv_custom_curated"

    print("=" * 65)
    print("STARTING RAPID MARITIME CUSTOM DETECTOR FINE-TUNING")
    print("=" * 65)

    model = YOLO(base_model)
    results = model.train(
        data=data_yaml,
        epochs=2,
        imgsz=1024,
        batch=4,
        device=0,
        workers=0,
        amp=True,
        lr0=0.0001,
        lrf=0.1,
        weight_decay=0.0005,
        flipud=0.5,
        fliplr=0.5,
        degrees=10.0,
        mosaic=0.0,      # disable mosaic so full vessel geometry is pristine
        close_mosaic=0,
        project=project,
        name=name,
        exist_ok=True,
        verbose=True,
        save=True,
    )

    trained_best = Path(project) / name / "weights" / "best.pt"
    trained_last = Path(project) / name / "weights" / "last.pt"
    target = Path("models/weights/vhrv_custom_best.pt")

    chosen = trained_best if trained_best.exists() else trained_last
    if chosen.exists():
        shutil.copy2(str(chosen), str(target))
        print(f"\n[SUCCESS] Updated {target} from {chosen}")
    else:
        print("[WARN] Trained weights not found.")

if __name__ == "__main__":
    main()
