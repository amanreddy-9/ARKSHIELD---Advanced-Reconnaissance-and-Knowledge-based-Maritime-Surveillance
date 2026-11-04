from pathlib import Path
import json
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import convnext_tiny, ConvNeXt_Tiny_Weights

# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_ROOT = Path(r".\data\TITANIC-FGS-10\ImageNet\train")
VAL_ROOT = Path(r".\data\TITANIC-FGS-10\ImageNet\val")

OUTPUT_DIR = Path(r".\models\weights\convnext_tiny")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_DIR = Path(r".\outputs\convnext_tiny")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

EPOCHS = 5
BATCH_SIZE = 16
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
NUM_WORKERS = 0

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================================
# CLASSES
# ============================================================

EXPECTED_CLASSES = [
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

# ============================================================
# DATA TRANSFORMS
# ============================================================

weights = ConvNeXt_Tiny_Weights.DEFAULT

train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(8),
    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15,
        saturation=0.10
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# ============================================================
# DATASETS
# ============================================================

print("=" * 70)
print("CONVNEXT-TINY SHIP CLASSIFIER")
print("=" * 70)

print(f"Device: {DEVICE}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(
        f"GPU memory: "
        f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
    )

print("\nLoading datasets...")

train_dataset = datasets.ImageFolder(
    TRAIN_ROOT,
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    VAL_ROOT,
    transform=val_transform
)

print(f"Training images: {len(train_dataset)}")
print(f"Validation images: {len(val_dataset)}")

print(f"\nDetected classes:")
print(train_dataset.classes)

# ============================================================
# VERIFY CLASS ORDER
# ============================================================

if set(train_dataset.classes) != set(EXPECTED_CLASSES):
    raise RuntimeError(
        "Dataset classes do not match expected 10 classes.\n"
        f"Expected: {EXPECTED_CLASSES}\n"
        f"Found: {train_dataset.classes}"
    )

print("\nClass mapping:")
for idx, name in enumerate(train_dataset.classes):
    print(f"{idx}: {name}")

# ============================================================
# DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available()
)

# ============================================================
# MODEL
# ============================================================

print("\nLoading pretrained ConvNeXt-Tiny...")

model = convnext_tiny(weights=weights)

# Replace classification head
in_features = model.classifier[2].in_features

model.classifier[2] = nn.Linear(
    in_features,
    len(train_dataset.classes)
)

model = model.to(DEVICE)

# ============================================================
# LOSS / OPTIMIZER
# ============================================================

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY
)

scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=EPOCHS
)

# ============================================================
# TRAINING
# ============================================================

best_val_accuracy = 0.0
history = []

print("\nStarting training...")
print(f"Epochs: {EPOCHS}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Learning rate: {LEARNING_RATE}")
print("=" * 70)

start_time = time.time()

for epoch in range(EPOCHS):

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in train_loader:

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        running_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)

        correct += (predictions == labels).sum().item()
        total += labels.size(0)

    train_loss = running_loss / total
    train_accuracy = correct / total

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    model.eval()

    val_running_loss = 0.0
    val_correct = 0
    val_total = 0

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)

            loss = criterion(outputs, labels)

            val_running_loss += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)

            val_correct += (predictions == labels).sum().item()
            val_total += labels.size(0)

    val_loss = val_running_loss / val_total
    val_accuracy = val_correct / val_total

    scheduler.step()

    elapsed = time.time() - start_time

    print(
        f"\nEpoch {epoch + 1}/{EPOCHS}"
    )

    print(
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_accuracy * 100:.2f}%"
    )

    print(
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_accuracy * 100:.2f}%"
    )

    print(
        f"Elapsed: {elapsed / 60:.1f} min"
    )

    history.append({
        "epoch": epoch + 1,
        "train_loss": train_loss,
        "train_accuracy": train_accuracy,
        "val_loss": val_loss,
        "val_accuracy": val_accuracy,
    })

    # --------------------------------------------------------
    # SAVE BEST MODEL
    # --------------------------------------------------------

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy

        checkpoint_path = OUTPUT_DIR / "best.pt"

        torch.save({
            "model_state_dict": model.state_dict(),
            "class_names": train_dataset.classes,
            "epoch": epoch + 1,
            "val_accuracy": val_accuracy,
            "val_loss": val_loss,
        }, checkpoint_path)

        print(
            f"✓ Best model saved: {checkpoint_path}"
        )

# ============================================================
# SAVE FINAL MODEL
# ============================================================

final_path = OUTPUT_DIR / "last.pt"

torch.save({
    "model_state_dict": model.state_dict(),
    "class_names": train_dataset.classes,
    "epoch": EPOCHS,
}, final_path)

# ============================================================
# SAVE TRAINING HISTORY
# ============================================================

history_path = RESULTS_DIR / "training_history.json"

with open(history_path, "w") as f:
    json.dump(history, f, indent=2)

# ============================================================
# SUMMARY
# ============================================================

peak_memory = None

if torch.cuda.is_available():
    peak_memory = torch.cuda.max_memory_allocated() / 1024**3

print("\n" + "=" * 70)
print("CONVNEXT-TINY TRAINING COMPLETE")
print("=" * 70)

print(f"Best validation accuracy: {best_val_accuracy * 100:.2f}%")
print(f"Best checkpoint: {OUTPUT_DIR / 'best.pt'}")
print(f"Final checkpoint: {final_path}")
print(f"Training history: {history_path}")

if peak_memory is not None:
    print(f"Peak GPU memory: {peak_memory:.2f} GB")