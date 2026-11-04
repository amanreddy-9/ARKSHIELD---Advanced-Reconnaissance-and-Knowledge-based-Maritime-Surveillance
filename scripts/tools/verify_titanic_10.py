from pathlib import Path

root = Path(r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS-10\ImageNet")
extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

for split in ["train", "val", "test"]:
    print(f"\n===== {split.upper()} =====")

    total = 0

    for class_dir in sorted((root / split).iterdir()):
        if not class_dir.is_dir():
            continue

        count = sum(
            1 for p in class_dir.rglob("*")
            if p.suffix.lower() in extensions
        )

        total += count
        print(f"{class_dir.name:30} {count:5}")

    print(f"TOTAL: {total}")

print("\nDataset path:", root)
