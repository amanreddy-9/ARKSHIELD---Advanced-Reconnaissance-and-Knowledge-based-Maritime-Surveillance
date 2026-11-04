import torch


def decode_predictions(prediction, confidence_threshold=0.25):
    """
    Decode CustomYOLO predictions.

    The training loss stores:
        x_center, y_center, width, height
    as normalized values in [0, 1].

    Therefore the decoder uses the same normalized representation.
    """

    batch_size, channels, height, width = prediction.shape

    prediction = prediction.permute(0, 2, 3, 1).contiguous()

    tx = prediction[..., 0]
    ty = prediction[..., 1]
    tw = prediction[..., 2]
    th = prediction[..., 3]

    objectness = torch.sigmoid(prediction[..., 4])
    class_probability = torch.sigmoid(prediction[..., 5])

    confidence = objectness * class_probability

    # Grid coordinates
    grid_y, grid_x = torch.meshgrid(
        torch.arange(height, device=prediction.device),
        torch.arange(width, device=prediction.device),
        indexing="ij"
    )

    grid_x = grid_x.float()
    grid_y = grid_y.float()

    # Convert predictions to normalized coordinates.
    center_x = (torch.sigmoid(tx) + grid_x) / width
    center_y = (torch.sigmoid(ty) + grid_y) / height

    box_width = torch.sigmoid(tw)
    box_height = torch.sigmoid(th)

    x1 = center_x - box_width / 2
    y1 = center_y - box_height / 2
    x2 = center_x + box_width / 2
    y2 = center_y + box_height / 2

    # Keep coordinates inside image
    x1 = x1.clamp(0, 1)
    y1 = y1.clamp(0, 1)
    x2 = x2.clamp(0, 1)
    y2 = y2.clamp(0, 1)

    results = []

    for b in range(batch_size):

        mask = confidence[b] >= confidence_threshold

        boxes = torch.stack(
            [
                x1[b][mask] * 640,
                y1[b][mask] * 640,
                x2[b][mask] * 640,
                y2[b][mask] * 640
            ],
            dim=1
        )

        scores = confidence[b][mask]

        class_ids = torch.zeros(
            scores.shape,
            dtype=torch.long,
            device=prediction.device
        )

        results.append(
            {
                "boxes": boxes,
                "scores": scores,
                "class_ids": class_ids
            }
        )

    return results


if __name__ == "__main__":

    print("Testing corrected Custom YOLO decoder...")

    prediction = torch.randn(1, 6, 40, 40)

    results = decode_predictions(
        prediction,
        confidence_threshold=0.5
    )

    result = results[0]

    print("Decoder test successful")
    print("Boxes:", result["boxes"].shape)
    print("Scores:", result["scores"].shape)
    print("Classes:", result["class_ids"].shape)

    if len(result["boxes"]) > 0:
        print("First box:", result["boxes"][0])