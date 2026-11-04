import torch
from torch.utils.data import DataLoader

from models.custom_yolo.model import CustomYOLO
from models.custom_yolo.dataset import VHRVDataset
from models.custom_yolo.loss import CustomYOLOLoss


def collate_fn(batch):
    images = torch.stack([item[0] for item in batch])
    targets = [item[1] for item in batch]
    return images, targets


dataset = VHRVDataset(
    root="data/vhrv/vhrv",
    split="train",
    img_size=640
)

loader = DataLoader(
    dataset,
    batch_size=2,
    shuffle=False,
    num_workers=0,
    collate_fn=collate_fn
)

model = CustomYOLO(num_classes=1)
criterion = CustomYOLOLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

images, targets = next(iter(loader))

print("Images:", images.shape)
print("Targets:", [t.shape for t in targets])

before = next(model.parameters()).detach().clone()

optimizer.zero_grad()

predictions = model(images)
loss = criterion(predictions, targets)

print("Loss before backward:", loss.item())

loss.backward()

optimizer.step()

after = next(model.parameters()).detach().clone()

changed = not torch.equal(before, after)

print("Backward pass: SUCCESS")
print("Optimizer step: SUCCESS")
print("Weights changed:", changed)
