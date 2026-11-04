import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torchvision.models import ResNet18_Weights


# ============================================================
# CONFIG
# ============================================================

DATA_ROOT = Path(
    r"F:\OATrack-VLM_complete_project\OATrack-VLM\data\TITANIC-FGS-10\ImageNet"
)

OUTPUT_DIR = Path(
    r"F:\OATrack-VLM_complete_project\OATrack-VLM\models\weights"
)

BATCH_SIZE = 16
NUM_WORKERS = 0
NUM_CLASSES = 10
IMAGE_SIZE = 224


# ============================================================
# DEVICE
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("\n==============================================")
print(" TITANIC-FGS 10-CLASS CLASSIFIER")
print("==============================================")
print("Device:", device)
print("Dataset:", DATA_ROOT)


# ============================================================
# TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(8),
    transforms.ColorJitter(
        brightness=0.15,
        contrast=0.15
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# DATASETS
# ============================================================

train_dataset = datasets.ImageFolder(
    DATA_ROOT / "train",
    transform=train_transform
)

val_dataset = datasets.ImageFolder(
    DATA_ROOT / "val",
    transform=eval_transform
)

test_dataset = datasets.ImageFolder(
    DATA_ROOT / "test",
    transform=eval_transform
)

print("\nClasses:")
for i, name in enumerate(train_dataset.classes):
    print(f"  {i}: {name}")

print("\nDataset sizes:")
print("  Train:", len(train_dataset))
print("  Val:  ", len(val_dataset))
print("  Test: ", len(test_dataset))


# ============================================================
# LOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS
)


# ============================================================
# MODEL
# ============================================================

print("\nLoading pretrained ResNet-18...")

model = models.resnet18(
    weights=ResNet18_Weights.DEFAULT
)

model.fc = nn.Linear(
    model.fc.in_features,
    NUM_CLASSES
)

model = model.to(device)


# ============================================================
# LOSS + OPTIMIZER
# ============================================================

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=0.0001,
    weight_decay=0.0001
)


# ============================================================
# VALIDATION
# ============================================================

def evaluate(loader):

    model.eval()

    correct = 0
    total = 0
    loss_sum = 0.0

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            loss_sum += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)

            correct += (
                predictions == labels
            ).sum().item()

            total += labels.size(0)

    accuracy = correct / total
    avg_loss = loss_sum / total

    return avg_loss, accuracy


# ============================================================
# TRAIN
# ============================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--epochs",
    type=int,
    default=2
)

args = parser.parse_args()

best_val_accuracy = 0.0

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

print("\n==============================================")
print(" STARTING TRAINING")
print("==============================================")

for epoch in range(args.epochs):

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(train_loader):

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels
        )

        loss.backward()

        optimizer.step()

        running_loss += (
            loss.item() * images.size(0)
        )

        predictions = outputs.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

        if (batch_idx + 1) % 50 == 0:

            print(
                f"Epoch {epoch+1}/{args.epochs} "
                f"| Batch {batch_idx+1}/{len(train_loader)} "
                f"| Loss {loss.item():.4f}"
            )

    train_loss = running_loss / total
    train_accuracy = correct / total

    val_loss, val_accuracy = evaluate(
        val_loader
    )

    print("\n----------------------------------------------")
    print(
        f"Epoch {epoch+1}/{args.epochs}"
    )
    print(
        f"Train Loss: {train_loss:.4f}"
    )
    print(
        f"Train Accuracy: {train_accuracy*100:.2f}%"
    )
    print(
        f"Val Loss: {val_loss:.4f}"
    )
    print(
        f"Val Accuracy: {val_accuracy*100:.2f}%"
    )
    print("----------------------------------------------")

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = val_accuracy

        checkpoint = {
            "model_state_dict": model.state_dict(),
            "classes": train_dataset.classes,
            "num_classes": NUM_CLASSES,
            "image_size": IMAGE_SIZE,
            "val_accuracy": val_accuracy
        }

        checkpoint_path = (
            OUTPUT_DIR /
            "titanic_fgs10_resnet18_best.pt"
        )

        torch.save(
            checkpoint,
            checkpoint_path
        )

        print(
            "Saved best model:",
            checkpoint_path
        )


# ============================================================
# FINAL TEST
# ============================================================

print("\n==============================================")
print(" TEST EVALUATION")
print("==============================================")

checkpoint_path = (
    OUTPUT_DIR /
    "titanic_fgs10_resnet18_best.pt"
)

if checkpoint_path.exists():

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    test_loss, test_accuracy = evaluate(
        test_loader
    )

    print(
        f"Test Loss: {test_loss:.4f}"
    )

    print(
        f"Test Accuracy: {test_accuracy*100:.2f}%"
    )

else:

    print(
        "No checkpoint found."
    )

print("\nTraining complete.")
