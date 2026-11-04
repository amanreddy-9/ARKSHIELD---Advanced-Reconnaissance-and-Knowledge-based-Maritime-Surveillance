import torch
import torch.nn as nn
import torch.nn.functional as F


class FusionBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, 1, 1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True)
        )

    def forward(self, x):
        return self.conv(x)


class CustomNeck(nn.Module):
    def __init__(self):
        super().__init__()

        self.reduce_f4 = FusionBlock(256, 128)
        self.fuse_f3 = FusionBlock(256, 128)

        self.reduce_f3 = FusionBlock(128, 64)
        self.fuse_f2 = FusionBlock(128, 64)

        self.reduce_f2 = FusionBlock(64, 32)
        self.fuse_f1 = FusionBlock(64, 32)

    def forward(self, f1, f2, f3, f4):

        p4 = self.reduce_f4(f4)

        p4_up = F.interpolate(
            p4,
            size=f3.shape[-2:],
            mode="nearest"
        )

        p3 = self.fuse_f3(
            torch.cat([p4_up, f3], dim=1)
        )

        p3_small = self.reduce_f3(p3)

        p3_up = F.interpolate(
            p3_small,
            size=f2.shape[-2:],
            mode="nearest"
        )

        p2 = self.fuse_f2(
            torch.cat([p3_up, f2], dim=1)
        )

        p2_small = self.reduce_f2(p2)

        p2_up = F.interpolate(
            p2_small,
            size=f1.shape[-2:],
            mode="nearest"
        )

        p1 = self.fuse_f1(
            torch.cat([p2_up, f1], dim=1)
        )

        return p1, p2, p3, p4
