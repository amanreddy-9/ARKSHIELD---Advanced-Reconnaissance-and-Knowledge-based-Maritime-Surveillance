import torch

from models.custom_yolo.inference import run_inference
from models.custom_yolo.metrics import box_iou


def calculate_metrics(predictions, ground_truths, iou_threshold=0.5):
    """
    Calculate Precision, Recall and AP for one IoU threshold.
    """

    predictions = sorted(
        predictions,
        key=lambda x: x[1],
        reverse=True
    )

    total_gt = sum(
        len(boxes) for boxes in ground_truths.values()
    )

    matched = {
        image_id: [False] * len(boxes)
        for image_id, boxes in ground_truths.items()
    }

    tp = []
    fp = []

    for image_id, score, pred_box in predictions:

        gt_boxes = ground_truths.get(image_id, [])

        if not gt_boxes:
            tp.append(0)
            fp.append(1)
            continue

        gt_tensor = torch.tensor(
            gt_boxes,
            dtype=torch.float32
        )

        pred_tensor = torch.tensor(
            [pred_box],
            dtype=torch.float32
        )

        ious = box_iou(
            pred_tensor,
            gt_tensor
        )[0]

        best_iou, best_index = torch.max(ious, dim=0)

        index = best_index.item()

        if (
            best_iou.item() >= iou_threshold
            and not matched[image_id][index]
        ):
            tp.append(1)
            fp.append(0)
            matched[image_id][index] = True
        else:
            tp.append(0)
            fp.append(1)

    if total_gt == 0:
        return 0.0, 0.0, 0.0

    if not tp:
        return 0.0, 0.0, 0.0

    tp = torch.tensor(tp, dtype=torch.float32)
    fp = torch.tensor(fp, dtype=torch.float32)

    cumulative_tp = torch.cumsum(tp, dim=0)
    cumulative_fp = torch.cumsum(fp, dim=0)

    precision_curve = cumulative_tp / (
        cumulative_tp + cumulative_fp
    ).clamp(min=1e-7)

    recall_curve = cumulative_tp / total_gt

    final_precision = (
        cumulative_tp[-1]
        / (cumulative_tp[-1] + cumulative_fp[-1]).clamp(min=1e-7)
    ).item()

    final_recall = (
        cumulative_tp[-1] / total_gt
    ).item()

    # Precision envelope
    precision_envelope = precision_curve.clone()

    for i in range(len(precision_envelope) - 2, -1, -1):
        precision_envelope[i] = max(
            precision_envelope[i],
            precision_envelope[i + 1]
        )

    recall_points = torch.cat([
        torch.tensor([0.0]),
        recall_curve,
        torch.tensor([1.0])
    ])

    precision_points = torch.cat([
        precision_envelope[:1],
        precision_envelope,
        torch.tensor([0.0])
    ])

    ap = torch.trapz(
        precision_points,
        recall_points
    ).item()

    return final_precision, final_recall, max(0.0, min(1.0, ap))


def evaluate(
    model,
    dataset,
    confidence_threshold=0.01
):

    model.eval()

    predictions = []
    ground_truths = {}

    for image_id in range(len(dataset)):

        image, targets, image_path = dataset[image_id]

        ground_truths[image_id] = []

        for target in targets:

            _, xc, yc, w, h = target.tolist()

            x1 = (xc - w / 2) * 640
            y1 = (yc - h / 2) * 640
            x2 = (xc + w / 2) * 640
            y2 = (yc + h / 2) * 640

            ground_truths[image_id].append(
                [x1, y1, x2, y2]
            )

        image = image.unsqueeze(0)

        result = run_inference(
            model,
            image,
            confidence_threshold=confidence_threshold,
            iou_threshold=0.5
        )[0]

        for box, score in zip(
            result["boxes"],
            result["scores"]
        ):

            predictions.append(
                (
                    image_id,
                    score.item(),
                    box.tolist()
                )
            )

    precision50, recall50, ap50 = calculate_metrics(
        predictions,
        ground_truths,
        iou_threshold=0.50
    )

    aps = []

    for threshold in [
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95
    ]:

        _, _, ap = calculate_metrics(
            predictions,
            ground_truths,
            iou_threshold=threshold
        )

        aps.append(ap)

    map5095 = sum(aps) / len(aps)

    return {
        "precision": precision50,
        "recall": recall50,
        "map50": ap50,
        "map50_95": map5095
    }


if __name__ == "__main__":

    from models.custom_yolo.model import CustomYOLO
    from models.custom_yolo.dataset import VHRVDataset

    print("Testing VHRV evaluator...")

    dataset = VHRVDataset(
        root="data/vhrv/vhrv",
        split="test",
        img_size=640
    )

    model = CustomYOLO(num_classes=1)

    print("Test images:", len(dataset))

    metrics = evaluate(
        model,
        dataset,
        confidence_threshold=0.5
    )

    print("Evaluator test successful")
    print("Precision:", metrics["precision"])
    print("Recall:", metrics["recall"])
    print("mAP50:", metrics["map50"])
    print("mAP50-95:", metrics["map50_95"])
