import torch

from models.custom_yolo.model import CustomYOLO
from models.custom_yolo.decoder import decode_predictions
from models.custom_yolo.nms import nms


def run_inference(model, image, confidence_threshold=0.25, iou_threshold=0.5):
    model.eval()

    with torch.no_grad():
        predictions = model(image)

    final_results = []

    for batch_index in range(image.shape[0]):

        # IMPORTANT:
        # The current loss trains only predictions[0].
        # Therefore, evaluate only predictions[0].
        decoded = decode_predictions(
            predictions[0][batch_index:batch_index + 1],
            confidence_threshold=confidence_threshold
        )[0]

        boxes = decoded["boxes"]
        scores = decoded["scores"]
        class_ids = decoded["class_ids"]

        keep = nms(
            boxes,
            scores,
            iou_threshold=iou_threshold
        )

        final_results.append({
            "boxes": boxes[keep],
            "scores": scores[keep],
            "class_ids": class_ids[keep]
        })

    return final_results

if __name__ == "__main__":

    print("Testing complete custom YOLO inference pipeline...")

    model = CustomYOLO(num_classes=1)

    image = torch.randn(
        1,
        3,
        640,
        640
    )

    results = run_inference(
        model,
        image,
        confidence_threshold=0.5,
        iou_threshold=0.5
    )

    result = results[0]

    print("Inference test successful")
    print("Final boxes:", result["boxes"].shape)
    print("Final scores:", result["scores"].shape)
    print("Final classes:", result["class_ids"].shape)