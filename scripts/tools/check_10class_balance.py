from pathlib import Path

root = Path(r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS\TITANIC-FGS\ImageNet\train")

classes = [
    "Destroyer",
    "Frigate",
    "Aircraft_carrier",
    "Amphibious_assault_ship",
    "Cruiser",
    "Littoral_combat_ship",
    "Cruise_ship",
    "Oil_tanker",
    "Yacht",
    "Non_ship"
]

extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

counts = {}

for name in classes:
    folder = root / name
    counts[name] = sum(
        1 for p in folder.rglob("*")
        if p.suffix.lower() in extensions
    )

target = 1200

print("\n===== PROPOSED 10-CLASS DATASET =====\n")

for name in classes:
    count = counts[name]

    if count > target:
        action = f"downsample {count-target}"
    elif count < target:
        action = f"augment {target-count}"
    else:
        action = "no change"

    print(f"{name:30} {count:5} -> {target:5} | {action}")

print("\nOriginal selected images:", sum(counts.values()))
print("Target training images:", target * len(classes))
print("Target per class:", target)
