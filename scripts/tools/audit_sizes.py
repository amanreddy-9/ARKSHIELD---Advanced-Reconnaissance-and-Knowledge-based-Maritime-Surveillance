from pathlib import Path
from PIL import Image

root = Path(r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS\TITANIC-FGS\ImageNet\train")

extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("\n===== CLASS IMAGE SIZE SUMMARY =====\n")

for class_dir in sorted(root.iterdir()):
    if not class_dir.is_dir():
        continue

    files = [
        p for p in class_dir.rglob("*")
        if p.suffix.lower() in extensions
    ]

    if files:
        try:
            with Image.open(files[0]) as img:
                size = img.size
        except Exception:
            size = "ERROR"

        print(f"{class_dir.name:30} {len(files):5} images | sample size = {size}")
    else:
        print(f"{class_dir.name:30}     0 images")
