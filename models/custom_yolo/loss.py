import torch
import torch.nn as nn


class CustomYOLOLoss(nn.Module):
    """
    YOLO-style loss for the custom HBB detector.

    VHRV labels:
        class_id, x_center, y_center, width, height

    Coordinates are normalized to [0, 1].
    """

    def __init__(self, box_weight=5.0, obj_weight=1.0, cls_weight=1.0):
        super().__init__()

        self.box_weight = box_weight
        self.obj_weight = obj_weight
        self.cls_weight = cls_weight

        self.box_loss = nn.SmoothL1Loss(reduction="sum")
        self.cls_loss = nn.BCEWithLogitsLoss(reduction="sum")
        self.obj_loss = nn.BCEWithLogitsLoss(reduction="none")

    def forward(self, predictions, targets):

        prediction = predictions[0]

        batch_size, _, height, width = prediction.shape

        prediction = prediction.permute(0, 2, 3, 1).contiguous()

        box_pred = prediction[..., 0:4]
        obj_pred = prediction[..., 4]
        cls_pred = prediction[..., 5]

        obj_target = torch.zeros_like(obj_pred)
        box_target = torch.zeros_like(box_pred)
        cls_target = torch.zeros_like(cls_pred)

        for b in range(batch_size):

            image_targets = targets[b]

            if image_targets.numel() == 0:
                continue

            for target in image_targets:

                class_id, xc, yc, w, h = target

                # Find grid cell containing the object center
                gx = min(width - 1, max(0, int(xc.item() * width)))
                gy = min(height - 1, max(0, int(yc.item() * height)))

                # Position inside that grid cell
                local_x = xc * width - gx
                local_y = yc * height - gy

                obj_target[b, gy, gx] = 1.0

                box_target[b, gy, gx] = torch.stack(
                    [
                        local_x,
                        local_y,
                        w,
                        h
                    ]
                )

                cls_target[b, gy, gx] = class_id

        positive = obj_target == 1
        negative = obj_target == 0

        total_box = torch.tensor(0.0, device=prediction.device)
        total_cls = torch.tensor(0.0, device=prediction.device)

        if positive.any():

            predicted_boxes = torch.sigmoid(box_pred[positive])

            total_box = self.box_loss(
                predicted_boxes,
                box_target[positive]
            )

            total_cls = self.cls_loss(
                cls_pred[positive],
                cls_target[positive]
            )

        # Use much stronger negative suppression.
        positive_obj = self.obj_loss(
            obj_pred[positive],
            obj_target[positive]
        )

        negative_obj = self.obj_loss(
            obj_pred[negative],
            obj_target[negative]
        )

        if positive_obj.numel() > 0:
            positive_obj = positive_obj.mean()
        else:
            positive_obj = torch.tensor(
                0.0,
                device=prediction.device
            )

        if negative_obj.numel() > 0:
            negative_obj = negative_obj.mean()
        else:
            negative_obj = torch.tensor(
                0.0,
                device=prediction.device
            )

        total_obj = positive_obj + negative_obj

        total_loss = (
            self.box_weight * total_box
            + self.obj_weight * total_obj
            + self.cls_weight * total_cls
        )

        return total_loss


if __name__ == "__main__":

    from models.custom_yolo.model import CustomYOLO

    print("Testing custom YOLO loss...")

    model = CustomYOLO(num_classes=1)

    images = torch.randn(2, 3, 640, 640)

    targets = [
        torch.tensor([
            [0.0, 0.20, 0.30, 0.10, 0.08],
            [0.0, 0.70, 0.60, 0.15, 0.12]
        ]),
        torch.tensor([
            [0.0, 0.40, 0.50, 0.08, 0.10]
        ])
    ]

    predictions = model(images)

    criterion = CustomYOLOLoss()

    loss = criterion(predictions, targets)

    print("Loss:", loss.item())
    print("Loss finite:", torch.isfinite(loss).item())

    loss.backward()

    print("Backward pass: SUCCESS")