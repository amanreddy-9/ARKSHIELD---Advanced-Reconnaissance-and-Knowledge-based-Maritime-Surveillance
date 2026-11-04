from pathlib import Path
from PIL import Image

root = Path(r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS\TITANIC-FGS\ImageNet")

extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

checked = 0
bad = []

for class_dir in root.joinpath("train").iterdir():
    if not class_dir.is_dir():
        continue

    files = [
        p for p in class_dir.rglob("*")
        if p.suffix.lower() in extensions
    ][:5]

    for p in files:
        checked += 1
        try:
            with Image.open(p) as img:
                img.verify()
        except Exception as e:
            bad.append((str(p), str(e)))

print("\n===== QUICK IMAGE CHECK =====")
print("Images checked:", checked)
print("Corrupt images:", len(bad))

if bad:
    for path, error in bad:
        print(path)
        print(error)
else:
    print("No problems found in sampled images.")
