"""
training/train_custom_detector.py
Phase 2: Custom Maritime YOLO Detector Training Pipeline
Trains an enhanced maritime vessel detector on VHRV dataset with:
- Higher spatial resolution (imgsz=1024) to eliminate small-vessel truncation
- Full aerial orientation invariance (vertical flip flipud=0.5, fliplr=0.5, rotation)
- Optimized maritime scale augmentation and anchor matching
- RTX 3050 4GB VRAM optimization (AMP enabled, workers=0 for Windows)
- Dedicated output target: models/weights/vhrv_custom_best.pt (preserves baseline vhrv_best.pt)
"""
import argparse
import shutil
from pathlib import Path
from ultralytics import YOLO


def train_custom_detector(
    base_weights="yolo11n.pt",
    data_yaml="data/vhrv/vhrv/vhrv.yaml",
    epochs=10,
    imgsz=1024,
    batch=2,
    device=0,
    project="runs/detect",
    name="vhrv_custom",
):
    print("=" * 65)
    print("PHASE 2: TRAINING CUSTOM MARITIME YOLO DETECTOR")
    print(f"Base Model: {base_weights} | Data: {data_yaml}")
    print(f"Epochs: {epochs} | Resolution: {imgsz}x{imgsz} | Batch: {batch}")
    print("=" * 65)

    model = YOLO(base_weights)

    # Train with maritime-optimized hyperparameters
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        workers=0,            # Windows multiprocessing stability
        amp=True,             # Mixed precision for RTX 3050 4GB VRAM
        flipud=0.5,           # Crucial for orientation-invariant maritime aerial views
        fliplr=0.5,
        degrees=45.0,         # Rotation augmentation for arbitrary vessel headings
        scale=0.5,
        mosaic=0.8,
        close_mosaic=3,
        project=project,
        name=name,
        exist_ok=True,
        verbose=True,
        save=True,
    )

    # Export best model to models/weights/vhrv_custom_best.pt
    target_dir = Path("models/weights")
    target_dir.mkdir(parents=True, exist_ok=True)
    custom_best_path = target_dir / "vhrv_custom_best.pt"

    trained_best = Path(project) / name / "weights" / "best.pt"
    if trained_best.exists():
        shutil.copy2(str(trained_best), str(custom_best_path))
        print(f"\nSuccessfully copied best custom weights to: {custom_best_path}")
    else:
        last_pt = Path(project) / name / "weights" / "last.pt"
        if last_pt.exists():
            shutil.copy2(str(last_pt), str(custom_best_path))
            print(f"\nCopied last weights to: {custom_best_path}")

    print("Phase 2 custom detector training completed.")
    return custom_best_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--base", default="yolo11n.pt")
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    train_custom_detector(
        base_weights=args.base,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
    )
