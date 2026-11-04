import torch
import torch.nn as nn


class DetectionHead(nn.Module):
    def __init__(self, num_classes=1):
        super().__init__()

        self.num_outputs = 5 + num_classes

        self.head_p1 = nn.Conv2d(32, self.num_outputs, 1)
        self.head_p2 = nn.Conv2d(64, self.num_outputs, 1)
        self.head_p3 = nn.Conv2d(128, self.num_outputs, 1)
        self.head_p4 = nn.Conv2d(128, self.num_outputs, 1)

    def forward(self, p1, p2, p3, p4):
        y1 = self.head_p1(p1)
        y2 = self.head_p2(p2)
        y3 = self.head_p3(p3)
        y4 = self.head_p4(p4)

        return y1, y2, y3, y4
