from pathlib import Path
from PIL import Image

root = Path(r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS\TITANIC-FGS\ImageNet")

extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

total = 0
bad = []

for p in root.rglob("*"):
    if p.suffix.lower() not in extensions:
        continue

    total += 1

    try:
        with Image.open(p) as img:
            img.verify()
    except Exception as e:
        bad.append((str(p), str(e)))

print("\n===== IMAGE INTEGRITY CHECK =====")
print("Total images:", total)
print("Corrupt images:", len(bad))

if bad:
    print("\nCorrupt files:")
    for path, error in bad[:50]:
        print(path)
        print("Error:", error)
else:
    print("No corrupt images found.")
