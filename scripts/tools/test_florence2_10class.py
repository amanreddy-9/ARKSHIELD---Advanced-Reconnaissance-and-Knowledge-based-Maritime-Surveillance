import os
import torch
from PIL import Image
from models.florence2_vlm import Florence2VLM


TEST_ROOT = r".\data\TITANIC-FGS-10\ImageNet\test"

CLASSES = [
    "Aircraft_carrier",
    "Amphibious_assault_ship",
    "Cruiser",
    "Destroyer",
    "Frigate",
    "Littoral_combat_ship",
    "Cruise_ship",
    "Oil_tanker",
    "Yacht",
    "Non_ship",
]


def clean_output(text):
    text = text.replace("</s>", "")
    text = text.replace("<s>", "")
    return text.strip()


vlm = Florence2VLM()

print("\n" + "=" * 70)
print("FLORENCE-2 10-CLASS BASELINE TEST")
print("=" * 70)

results = []

for class_name in CLASSES:

    folder = os.path.join(TEST_ROOT, class_name)

    images = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not images:
        print(f"\n{class_name}: NO IMAGES")
        continue

    # Test 2 images per class initially
    images = sorted(images)[:2]

    for filename in images:

        image_path = os.path.join(folder, filename)

        try:
            output = vlm.generate(
                image_path,
                task="<CAPTION>",
                max_new_tokens=80
            )

            output = clean_output(output)

            print(f"\nActual class : {class_name}")
            print(f"Image        : {filename}")
            print(f"Florence-2   : {output}")

            results.append({
                "actual": class_name,
                "image": filename,
                "output": output
            })

        except Exception as e:
            print(f"\nERROR: {image_path}")
            print(e)


print("\n" + "=" * 70)
print(f"Images tested: {len(results)}")
print("=" * 70)

if torch.cuda.is_available():
    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )