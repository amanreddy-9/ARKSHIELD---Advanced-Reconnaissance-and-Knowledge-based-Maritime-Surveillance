from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import random
import shutil

# ============================================================
# PATHS
# ============================================================

SOURCE = Path(
    r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS\TITANIC-FGS\ImageNet"
)

DEST = Path(
    r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS-10\ImageNet"
)

# ============================================================
# SETTINGS
# ============================================================

CLASSES = [
    "Destroyer",
    "Frigate",
    "Aircraft_carrier",
    "Amphibious_assault_ship",
    "Cruiser",
    "Littoral_combat_ship",
    "Cruise_ship",
    "Oil_tanker",
    "Yacht",
    "Non_ship",
]

TARGET = 1200
SEED = 42

EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

random.seed(SEED)


# ============================================================
# HELPER
# ============================================================

def get_images(folder):
    return sorted([
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    ])


def augment_image(source_path, output_path):
    with Image.open(source_path) as img:
        img = img.convert("RGB")

        # Random horizontal flip
        if random.random() < 0.5:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Small rotation
        angle = random.uniform(-8, 8)
        img = img.rotate(
            angle,
            resample=Image.Resampling.BILINEAR,
            expand=True
        )

        # Random crop back to original aspect ratio
        w, h = img.size

        if w > 20 and h > 20:
            crop_factor = random.uniform(0.90, 1.0)

            new_w = int(w * crop_factor)
            new_h = int(h * crop_factor)

            left = random.randint(0, max(0, w - new_w))
            top = random.randint(0, max(0, h - new_h))

            img = img.crop(
                (left, top, left + new_w, top + new_h)
            )

        # Brightness
        brightness = random.uniform(0.85, 1.15)
        img = ImageEnhance.Brightness(img).enhance(brightness)

        # Contrast
        contrast = random.uniform(0.85, 1.15)
        img = ImageEnhance.Contrast(img).enhance(contrast)

        # Slight blur sometimes
        if random.random() < 0.15:
            img = img.filter(
                ImageFilter.GaussianBlur(
                    radius=random.uniform(0.2, 0.6)
                )
            )

        # Save as JPEG
        img.save(
            output_path,
            format="JPEG",
            quality=95
        )


# ============================================================
# CREATE DIRECTORIES
# ============================================================

print("\n==============================================")
print(" TITANIC-FGS 10-CLASS DATASET PREPARATION")
print("==============================================\n")

DEST.mkdir(parents=True, exist_ok=True)

for split in ["train", "val", "test"]:
    for class_name in CLASSES:
        (DEST / split / class_name).mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# TRAINING DATA
# ============================================================

print("===== PREPARING TRAINING DATA =====\n")

for class_name in CLASSES:

    source_dir = SOURCE / "train" / class_name
    dest_dir = DEST / "train" / class_name

    images = get_images(source_dir)

    print(
        f"{class_name:30} "
        f"original = {len(images):4} "
        f"target = {TARGET}"
    )

    if len(images) >= TARGET:

        # Downsample
        selected = random.sample(images, TARGET)

        for i, src in enumerate(selected):
            extension = src.suffix.lower()

            dst = dest_dir / f"{i:05d}{extension}"

            shutil.copy2(src, dst)

    else:

        # Keep all original images
        for i, src in enumerate(images):

            extension = src.suffix.lower()

            dst = dest_dir / f"{i:05d}{extension}"

            shutil.copy2(src, dst)

        # Generate augmented images
        required = TARGET - len(images)

        print(
            f"{'':30} "
            f"augmenting = {required}"
        )

        for i in range(required):

            src = random.choice(images)

            dst = dest_dir / (
                f"aug_{i:05d}.jpg"
            )

            augment_image(src, dst)

    final_count = len(get_images(dest_dir))

    print(
        f"{'':30} "
        f"final = {final_count}"
    )


# ============================================================
# VALIDATION + TEST
# ============================================================

print("\n===== COPYING VALIDATION AND TEST =====\n")

for split in ["val", "test"]:

    print(f"--- {split.upper()} ---")

    for class_name in CLASSES:

        source_dir = SOURCE / split / class_name
        dest_dir = DEST / split / class_name

        images = get_images(source_dir)

        for src in images:

            dst = dest_dir / src.name

            shutil.copy2(src, dst)

        print(
            f"{class_name:30} "
            f"{len(images):4} images"
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n==============================================")
print(" FINAL DATASET SUMMARY")
print("==============================================\n")

for split in ["train", "val", "test"]:

    total = 0

    print(f"{split.upper()}:")

    for class_name in CLASSES:

        count = len(
            get_images(
                DEST / split / class_name
            )
        )

        total += count

        print(
            f"  {class_name:28} {count:4}"
        )

    print(f"  TOTAL: {total}\n")

print("Dataset created successfully.")
print(f"Location: {DEST}")
print(f"Random seed: {SEED}")
