import torch
import torch.nn as nn

from .backbone import CustomBackbone
from .neck import CustomNeck
from .head import DetectionHead


class CustomYOLO(nn.Module):
    def __init__(self, num_classes=1):
        super().__init__()

        self.backbone = CustomBackbone()
        self.neck = CustomNeck()
        self.head = DetectionHead(num_classes)

    def forward(self, x):
        features = self.backbone(x)
        fused = self.neck(*features)
        predictions = self.head(*fused)

        return predictions


if __name__ == "__main__":
    model = CustomYOLO(num_classes=1)

    x = torch.randn(1, 3, 640, 640)

    outputs = model(x)

    print("CustomYOLO test successful")
    print("Output shapes:")
    for output in outputs:
        print(output.shape)
