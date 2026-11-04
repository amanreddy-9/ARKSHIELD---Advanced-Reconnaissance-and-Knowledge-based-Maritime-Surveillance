from pathlib import Path
import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import convnext_tiny

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

# ============================================================
# PATHS
# ============================================================

TEST_ROOT = Path(r".\data\TITANIC-FGS-10\ImageNet\test")
CHECKPOINT = Path(r".\models\weights\convnext_tiny\best.pt")
OUTPUT_DIR = Path(r".\outputs\convnext_tiny")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RESULT_FILE = OUTPUT_DIR / "test_results.json"

BATCH_SIZE = 16
NUM_WORKERS = 0

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================================
# TRANSFORM
# ============================================================

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

# ============================================================
# DATASET
# ============================================================

print("=" * 70)
print("CONVNEXT-TINY TEST EVALUATION")
print("=" * 70)

print(f"Device: {DEVICE}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

test_dataset = datasets.ImageFolder(
    TEST_ROOT,
    transform=transform,
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
)

print(f"Test images: {len(test_dataset)}")
print(f"Classes: {test_dataset.classes}")

# ============================================================
# LOAD CHECKPOINT
# ============================================================

print("\nLoading ConvNeXt-Tiny checkpoint...")

checkpoint = torch.load(
    CHECKPOINT,
    map_location=DEVICE,
    weights_only=False,
)

model = convnext_tiny(weights=None)

in_features = model.classifier[2].in_features

model.classifier[2] = nn.Linear(
    in_features,
    len(test_dataset.classes),
)

model.load_state_dict(checkpoint["model_state_dict"])

model = model.to(DEVICE)
model.eval()

print(
    f"Checkpoint epoch: "
    f"{checkpoint.get('epoch', 'unknown')}"
)

print(
    f"Checkpoint validation accuracy: "
    f"{checkpoint.get('val_accuracy', 0) * 100:.2f}%"
)

# ============================================================
# PREDICTION
# ============================================================

all_labels = []
all_predictions = []

print("\nRunning test inference...")

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(DEVICE)

        outputs = model(images)

        predictions = outputs.argmax(dim=1).cpu()

        all_predictions.extend(predictions.tolist())
        all_labels.extend(labels.tolist())

# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    all_labels,
    all_predictions,
)

precision, recall, f1, _ = precision_recall_fscore_support(
    all_labels,
    all_predictions,
    average="weighted",
    zero_division=0,
)

report = classification_report(
    all_labels,
    all_predictions,
    target_names=test_dataset.classes,
    output_dict=True,
    zero_division=0,
)

matrix = confusion_matrix(
    all_labels,
    all_predictions,
)

# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("TEST RESULTS")
print("=" * 70)

print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Recall:    {recall * 100:.2f}%")
print(f"F1-score:  {f1 * 100:.2f}%")

print("\nClassification report:")
print(
    classification_report(
        all_labels,
        all_predictions,
        target_names=test_dataset.classes,
        zero_division=0,
    )
)

print("\nConfusion matrix:")
print("Rows = actual class")
print("Columns = predicted class")
print(matrix)

# ============================================================
# SAVE RESULTS
# ============================================================

results = {
    "model": "ConvNeXt-Tiny",
    "checkpoint": str(CHECKPOINT),
    "checkpoint_epoch": checkpoint.get("epoch"),
    "validation_accuracy": checkpoint.get("val_accuracy"),
    "test_images": len(test_dataset),
    "classes": test_dataset.classes,
    "accuracy": accuracy,
    "weighted_precision": precision,
    "weighted_recall": recall,
    "weighted_f1": f1,
    "classification_report": report,
    "confusion_matrix": matrix.tolist(),
}

with open(RESULT_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDetailed results saved to:")
print(RESULT_FILE)

print("\n" + "=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)