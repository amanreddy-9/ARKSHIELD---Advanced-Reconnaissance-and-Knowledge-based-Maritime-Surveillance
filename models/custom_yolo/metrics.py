import torch


def box_iou(boxes1, boxes2):
    """
    Calculate pairwise IoU between two sets of boxes.

    Boxes format:
    [x1, y1, x2, y2]
    """

    if boxes1.numel() == 0 or boxes2.numel() == 0:
        return torch.zeros(
            (boxes1.shape[0], boxes2.shape[0]),
            device=boxes1.device
        )

    area1 = (
        (boxes1[:, 2] - boxes1[:, 0]).clamp(min=0)
        *
        (boxes1[:, 3] - boxes1[:, 1]).clamp(min=0)
    )

    area2 = (
        (boxes2[:, 2] - boxes2[:, 0]).clamp(min=0)
        *
        (boxes2[:, 3] - boxes2[:, 1]).clamp(min=0)
    )

    top_left = torch.maximum(
        boxes1[:, None, :2],
        boxes2[None, :, :2]
    )

    bottom_right = torch.minimum(
        boxes1[:, None, 2:],
        boxes2[None, :, 2:]
    )

    intersection_wh = (
        bottom_right - top_left
    ).clamp(min=0)

    intersection = (
        intersection_wh[..., 0]
        *
        intersection_wh[..., 1]
    )

    union = (
        area1[:, None]
        + area2[None, :]
        - intersection
    )

    return intersection / union.clamp(min=1e-7)


if __name__ == "__main__":

    boxes1 = torch.tensor([
        [0., 0., 100., 100.]
    ])

    boxes2 = torch.tensor([
        [50., 50., 150., 150.]
    ])

    iou = box_iou(boxes1, boxes2)

    print("IoU test successful")
    print("IoU:", iou.item())
