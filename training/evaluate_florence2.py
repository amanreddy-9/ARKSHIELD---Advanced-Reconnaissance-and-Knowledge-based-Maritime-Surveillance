import os
import re
import json
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from peft import PeftModel
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

# ============================================================
# CONFIG
# ============================================================

MODEL_ID = "microsoft/Florence-2-base"

ADAPTER_PATH = r".\models\weights\florence2_classifier_lora"

TEST_ROOT = r".\data\TITANIC-FGS-10\ImageNet\test"

RESULTS_PATH = r".\outputs\florence2_test_results.json"

MAX_NEW_TOKENS = 80

# ============================================================
# 10 CLASSES
# ============================================================

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

# Human-readable names
CLASS_DISPLAY = {
    "Aircraft_carrier": "Aircraft carrier",
    "Amphibious_assault_ship": "Amphibious assault ship",
    "Cruiser": "Cruiser",
    "Destroyer": "Destroyer",
    "Frigate": "Frigate",
    "Littoral_combat_ship": "Littoral combat ship",
    "Cruise_ship": "Cruise ship",
    "Oil_tanker": "Oil tanker",
    "Yacht": "Yacht",
    "Non_ship": "Non ship",
}


# ============================================================
# DEVICE
# ============================================================

device = "cuda" if torch.cuda.is_available() else "cpu"

print("=" * 70)
print("FLORENCE-2 10-CLASS TEST EVALUATION")
print("=" * 70)

print("Device:", device)

if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))


# ============================================================
# LOAD PROCESSOR
# ============================================================

print("\nLoading processor...")

processor = AutoProcessor.from_pretrained(
    MODEL_ID,
    trust_remote_code=True
)


# ============================================================
# LOAD BASE MODEL
# ============================================================

print("Loading Florence-2 base model...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    attn_implementation="eager",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)

model = model.to(device)


# ============================================================
# LOAD LoRA ADAPTER
# ============================================================

print("Loading LoRA adapter...")

model = PeftModel.from_pretrained(
    model,
    ADAPTER_PATH
)

model = model.to(device)

model.eval()

print("Florence-2 + LoRA loaded successfully.")


# ============================================================
# BUILD TEST SET
# ============================================================

samples = []

for class_name in CLASSES:

    class_dir = os.path.join(
        TEST_ROOT,
        class_name
    )

    if not os.path.isdir(class_dir):

        print(
            "WARNING: Missing class directory:",
            class_dir
        )

        continue

    for filename in os.listdir(class_dir):

        if filename.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        ):

            samples.append(
                {
                    "image": os.path.join(
                        class_dir,
                        filename
                    ),
                    "label": class_name
                }
            )


print("\nTotal test images:", len(samples))

# ============================================================
# PROMPT
# ============================================================

QUESTION = (
    "What is the fine-grained type of ship in this image? "
    "Choose exactly one of these classes: "
    "Aircraft carrier, Amphibious assault ship, Cruiser, "
    "Destroyer, Frigate, Littoral combat ship, Cruise ship, "
    "Oil tanker, Yacht, Non ship. "
    "Answer with only the class name."
)


# ============================================================
# NORMALIZE MODEL OUTPUT
# ============================================================

def normalize_prediction(text):

    text = text.lower().strip()

    # Remove common Florence special tokens
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize punctuation
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Important:
    # Check longer / more specific names first.

    aliases = [
        (
            "amphibious assault ship",
            "Amphibious_assault_ship"
        ),
        (
            "littoral combat ship",
            "Littoral_combat_ship"
        ),
        (
            "aircraft carrier",
            "Aircraft_carrier"
        ),
        (
            "cruise ship",
            "Cruise_ship"
        ),
        (
            "oil tanker",
            "Oil_tanker"
        ),
        (
            "destroyer",
            "Destroyer"
        ),
        (
            "frigate",
            "Frigate"
        ),
        (
            "cruiser",
            "Cruiser"
        ),
        (
            "yacht",
            "Yacht"
        ),
        (
            "non ship",
            "Non_ship"
        ),
        (
            "nonship",
            "Non_ship"
        ),
    ]

    for phrase, class_name in aliases:

        if phrase in text:
            return class_name

    return None


# ============================================================
# PREDICTION
# ============================================================

y_true = []
y_pred = []

results = []

print("\nStarting inference...")
print("=" * 70)

for index, sample in enumerate(samples):

    image_path = sample["image"]
    true_label = sample["label"]

    try:

        image = Image.open(
            image_path
        ).convert("RGB")

        prompt = "<VQA> " + QUESTION

        inputs = processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )

        inputs = {
            key: value.to(device)
            if hasattr(value, "to")
            else value
            for key, value in inputs.items()
        }

        if device == "cuda" and "pixel_values" in inputs:
            inputs["pixel_values"] = inputs["pixel_values"].half()

        with torch.no_grad():

            generated_ids = model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=MAX_NEW_TOKENS,
                num_beams=1,
                use_cache=False
            )

        generated_text = processor.batch_decode(
            generated_ids,
            skip_special_tokens=False
        )[0]

        predicted_label = normalize_prediction(
            generated_text
        )

        y_true.append(true_label)

        if predicted_label is None:

            y_pred.append("Unknown")

        else:

            y_pred.append(predicted_label)

        results.append(
            {
                "image": os.path.basename(image_path),
                "true_label": true_label,
                "raw_output": generated_text,
                "predicted_label": predicted_label,
            }
        )

        if (index + 1) % 50 == 0:

            print(
                f"Processed {index + 1}/{len(samples)}"
            )

    except Exception as e:

        print(
            f"ERROR: {os.path.basename(image_path)}"
        )

        print(str(e))

        y_true.append(true_label)
        y_pred.append("Unknown")

        results.append(
            {
                "image": os.path.basename(image_path),
                "true_label": true_label,
                "raw_output": "",
                "predicted_label": None,
                "error": str(e),
            }
        )


# ============================================================
# METRICS
# ============================================================

print("\n")
print("=" * 70)
print("RESULTS")
print("=" * 70)

accuracy = accuracy_score(
    y_true,
    y_pred
)

precision, recall, f1, _ = precision_recall_fscore_support(
    y_true,
    y_pred,
    labels=CLASSES,
    average="weighted",
    zero_division=0
)

print(
    f"\nAccuracy:  {accuracy * 100:.2f}%"
)

print(
    f"Precision: {precision * 100:.2f}%"
)

print(
    f"Recall:    {recall * 100:.2f}%"
)

print(
    f"F1-score:  {f1 * 100:.2f}%"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification report:\n")

print(
    classification_report(
        y_true,
        y_pred,
        labels=CLASSES,
        target_names=[
            CLASS_DISPLAY[c]
            for c in CLASSES
        ],
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=CLASSES
)

print("\nConfusion matrix:")

print(
    "Rows = actual class"
)

print(
    "Columns = predicted class"
)

print("\n", cm)


# ============================================================
# SAVE RESULTS
# ============================================================

os.makedirs(
    os.path.dirname(RESULTS_PATH),
    exist_ok=True
)

output = {
    "model": MODEL_ID,
    "adapter": ADAPTER_PATH,
    "test_images": len(samples),
    "accuracy": float(accuracy),
    "weighted_precision": float(precision),
    "weighted_recall": float(recall),
    "weighted_f1": float(f1),
    "classes": CLASSES,
    "confusion_matrix": cm.tolist(),
    "results": results,
}

with open(
    RESULTS_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2
    )

print("\nDetailed results saved to:")

print(RESULTS_PATH)

print("\nEvaluation complete.")