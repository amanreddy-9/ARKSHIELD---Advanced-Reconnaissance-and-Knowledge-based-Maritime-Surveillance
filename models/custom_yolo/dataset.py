from pathlib import Path
from PIL import Image
import torch
from torch.utils.data import Dataset


class VHRVDataset(Dataset):
    def __init__(self, root, split="train", img_size=640):
        self.root = Path(root)
        self.split = split
        self.img_size = img_size

        self.image_dir = self.root / "images" / split
        self.label_dir = self.root / "labels" / split

        extensions = {".jpg", ".jpeg", ".png", ".bmp"}

        self.images = sorted(
            [
                p for p in self.image_dir.iterdir()
                if p.suffix.lower() in extensions
            ]
        )

        if not self.images:
            raise RuntimeError(
                f"No images found in {self.image_dir}"
            )

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image_path = self.images[index]

        image = Image.open(image_path).convert("RGB")

        original_width, original_height = image.size

        image = image.resize(
            (self.img_size, self.img_size)
        )

        image = torch.from_numpy(
            __import__("numpy").array(image)
        ).permute(2, 0, 1).float() / 255.0

        label_path = self.label_dir / f"{image_path.stem}.txt"

        boxes = []

        if label_path.exists():
            with open(label_path, "r", encoding="utf-8") as f:
                for line in f:
                    values = line.strip().split()

                    if len(values) != 5:
                        continue

                    class_id, xc, yc, w, h = map(float, values)

                    boxes.append([
                        class_id,
                        xc,
                        yc,
                        w,
                        h
                    ])

        if boxes:
            targets = torch.tensor(
                boxes,
                dtype=torch.float32
            )
        else:
            targets = torch.zeros(
                (0, 5),
                dtype=torch.float32
            )

        return image, targets, str(image_path)


if __name__ == "__main__":
    dataset = VHRVDataset(
        root="data/vhrv/vhrv",
        split="train",
        img_size=640
    )

    print("VHRV Dataset test successful")
    print("Number of images:", len(dataset))

    image, targets, path = dataset[0]

    print("Image:", image.shape)
    print("Targets:", targets.shape)
    print("First image:", path)

    if len(targets) > 0:
        print("First target:", targets[0])
