import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from models.custom_yolo.model import CustomYOLO
from models.custom_yolo.dataset import VHRVDataset
from models.custom_yolo.loss import CustomYOLOLoss


def collate_fn(batch):
    images = torch.stack([item[0] for item in batch])
    targets = [item[1] for item in batch]
    paths = [item[2] for item in batch]
    return images, targets, paths


def train(
    epochs=1,
    batch_size=2,
    learning_rate=0.001,
    img_size=640,
    device="cpu"
):

    device = torch.device(device)

    print("========================================")
    print("Custom YOLO Training")
    print("========================================")
    print("Device:", device)
    print("Epochs:", epochs)
    print("Batch size:", batch_size)
    print("Learning rate:", learning_rate)
    print("Image size:", img_size)

    dataset = VHRVDataset(
        root="data/vhrv/vhrv",
        split="train",
        img_size=img_size
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        collate_fn=collate_fn
    )

    model = CustomYOLO(num_classes=1).to(device)

    criterion = CustomYOLOLoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=learning_rate
    )

    output_dir = Path("runs/custom_yolo")
    output_dir.mkdir(parents=True, exist_ok=True)

    history = []

    for epoch in range(epochs):

        model.train()

        epoch_loss = 0.0
        batches = 0

        print()
        print(
            f"Epoch {epoch + 1}/{epochs}"
        )

        for images, targets, _ in loader:

            images = images.to(device)

            targets = [
                target.to(device)
                for target in targets
            ]

            optimizer.zero_grad()

            predictions = model(images)

            loss = criterion(
                predictions,
                targets
            )

            loss.backward()

            optimizer.step()

            epoch_loss += loss.item()
            batches += 1

            if batches % 50 == 0:
                print(
                    f"  Batch {batches}/{len(loader)} "
                    f"Loss: {loss.item():.4f}"
                )

        average_loss = epoch_loss / max(batches, 1)

        history.append({
            "epoch": epoch + 1,
            "loss": average_loss
        })

        print(
            f"Epoch {epoch + 1} complete "
            f"| Average Loss: {average_loss:.4f}"
        )

        checkpoint = output_dir / f"custom_yolo_epoch_{epoch + 1}.pt"

        torch.save(
            {
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": average_loss
            },
            checkpoint
        )

        print("Checkpoint saved:", checkpoint)

    history_file = output_dir / "training_history.json"

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    final_model = output_dir / "custom_yolo_final.pt"

    torch.save(
        model.state_dict(),
        final_model
    )

    print()
    print("========================================")
    print("Training completed successfully")
    print("========================================")
    print("Final model:", final_model)
    print("Training history:", history_file)

    return model, history


if __name__ == "__main__":

    train(
        epochs=1,
        batch_size=2,
        learning_rate=0.001,
        img_size=640,
        device="cpu"
    )
