"""
training/evaluate_detector.py
Comprehensive Evaluation & Diagnostic Script for YOLO Vessel Detectors
Generates un-fabricated evaluation metrics and visual comparisons.
"""
import argparse
import json
import math
from pathlib import Path
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO


def bbox_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])

    inter = max(0.0, xB - xA) * max(0.0, yB - yA)
    a1 = max(0.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    a2 = max(0.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0.0


def evaluate_detector(
    model_path="models/weights/vhrv_best.pt",
    data_yaml="data/vhrv/vhrv/vhrv.yaml",
    split="test",
    imgsz=1024,
    conf=0.25,
    iou=0.60,
    device=0,
    save_diagnostics=True,
    output_dir="outputs/diagnostics",
):
    model_path = str(Path(model_path))
    output_dir = Path(output_dir)
    gt_vs_pred_dir = output_dir / "ground_truth_vs_prediction"
    multi_ship_dir = output_dir / "multi_ship_tests"

    gt_vs_pred_dir.mkdir(parents=True, exist_ok=True)
    multi_ship_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print(f"EVALUATING DETECTOR: {model_path}")
    print(f"Data: {data_yaml} | Split: {split} | ImgSz: {imgsz} | Conf: {conf} | IoU: {iou}")
    print("=" * 65)

    model = YOLO(model_path)

    # 1. Standard Ultralytics Validation for certified COCO metrics
    val_results = model.val(
        data=data_yaml,
        split=split,
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        batch=2,
        device=device,
        workers=0,
        verbose=False,
    )

    p = float(val_results.results_dict.get("metrics/precision(B)", 0.0))
    r = float(val_results.results_dict.get("metrics/recall(B)", 0.0))
    map50 = float(val_results.results_dict.get("metrics/mAP50(B)", 0.0))
    map50_95 = float(val_results.results_dict.get("metrics/mAP50-95(B)", 0.0))
    speed = val_results.speed

    inf_ms = float(speed.get("inference", 0.0))
    fps = round(1000.0 / inf_ms, 2) if inf_ms > 0 else 0.0

    # 2. Detailed Instance-Level & Localization Diagnostic on Test Set
    data_root = Path(data_yaml).parent
    img_dir = data_root / "images" / split
    lbl_dir = data_root / "labels" / split

    img_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
    total_gt = 0
    total_pred = 0
    true_positives = 0
    false_positives = 0
    matched_ious = []

    # Selected representative samples for visual diagnostic exports
    diagnostic_stems = {
        "vhrv_00038": "multi_ship",
        "vhrv_00050": "standard",
        "vhrv_00113": "multi_ship",
        "vhrv_01045": "dense_anchorage",
        "vhrv_01229": "dense_anchorage",
        "vhrv_00093": "isolated",
    }

    for img_p in img_files:
        lbl_p = lbl_dir / (img_p.stem + ".txt")
        gt_boxes = []

        with Image.open(img_p) as im:
            W, H = im.size

        if lbl_p.exists():
            with open(lbl_p, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cx = float(parts[1]) * W
                        cy = float(parts[2]) * H
                        w = float(parts[3]) * W
                        h = float(parts[4]) * H
                        gt_boxes.append([cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0])

        total_gt += len(gt_boxes)

        res = model.predict(
            source=str(img_p),
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            device=device,
            verbose=False,
        )[0]

        pred_boxes = []
        for box in res.boxes:
            b = box.xyxy[0].tolist()
            c = float(box.conf.item())
            pred_boxes.append(b + [c])

        total_pred += len(pred_boxes)

        # Match preds to GT with IoU >= 0.50
        matched_gt = set()
        for pb in pred_boxes:
            best_iou = 0.0
            best_idx = -1
            for g_i, gb in enumerate(gt_boxes):
                if g_i in matched_gt:
                    continue
                iou_val = bbox_iou(pb[:4], gb)
                if iou_val > best_iou:
                    best_iou = iou_val
                    best_idx = g_i

            if best_iou >= 0.50 and best_idx != -1:
                true_positives += 1
                matched_gt.add(best_idx)
                matched_ious.append(best_iou)
            else:
                false_positives += 1

        # Generate Visual Diagnostic Image if selected
        if save_diagnostics and img_p.stem in diagnostic_stems:
            diag_tag = diagnostic_stems[img_p.stem]
            vis_img = Image.open(img_p).convert("RGB")
            draw = ImageDraw.Draw(vis_img)

            # Draw Ground Truth in Green
            for gb in gt_boxes:
                draw.rectangle(gb, outline=(0, 255, 100), width=4)

            # Draw Predictions in Cyan/Yellow with confidence and IoU
            for pb in pred_boxes:
                px1, py1, px2, py2, p_conf = pb
                # Find matching IoU
                max_iou = max([bbox_iou(pb[:4], gb) for gb in gt_boxes]) if gt_boxes else 0.0
                draw.rectangle([px1, py1, px2, py2], outline=(0, 230, 255), width=3)
                label_text = f"{p_conf:.0%} (IoU {max_iou:.2f})"
                draw.text((px1, max(0, py1 - 18)), label_text, fill=(255, 255, 255))

            # Resize to web/inspection friendly resolution
            preview_w = 1600
            preview_h = int(H * (preview_w / W))
            vis_preview = vis_img.resize((preview_w, preview_h), Image.Resampling.LANCZOS)

            dest_folder = multi_ship_dir if diag_tag in ("multi_ship", "dense_anchorage") else gt_vs_pred_dir
            vis_preview.save(dest_folder / f"eval_{img_p.stem}_{imgsz}px.jpg", quality=92)

    false_negatives = total_gt - true_positives
    mean_loc_iou = round(float(np.mean(matched_ious)), 4) if matched_ious else 0.0

    metrics = {
        "model_path": model_path,
        "split": split,
        "image_size": imgsz,
        "confidence_threshold": conf,
        "nms_iou_threshold": iou,
        "precision": round(p, 4),
        "recall": round(r, 4),
        "mAP50": round(map50, 4),
        "mAP50_95": round(map50_95, 4),
        "inference_ms": round(inf_ms, 2),
        "fps": fps,
        "total_ground_truth_vessels": total_gt,
        "total_predicted_vessels": total_pred,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "missed_detections": false_negatives,
        "mean_localization_iou": mean_loc_iou,
        "speed_breakdown": speed,
    }

    # Save to metrics JSON
    model_stem = Path(model_path).stem
    metrics_file = output_dir / f"metrics_{model_stem}_{imgsz}px.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 65)
    print("EVALUATION RESULTS (NO FABRICATED METRICS)")
    print("=" * 65)
    print(f"Precision:         {metrics['precision']:.2%}")
    print(f"Recall:            {metrics['recall']:.2%}")
    print(f"mAP@0.50:          {metrics['mAP50']:.2%}")
    print(f"mAP@0.50:0.95:     {metrics['mAP50_95']:.2%}")
    print(f"Mean Box IoU:      {metrics['mean_localization_iou']:.4f}")
    print(f"Inference Latency: {metrics['inference_ms']} ms ({metrics['fps']} FPS)")
    print(f"Ground Truth:      {metrics['total_ground_truth_vessels']} vessels")
    print(f"Predictions:       {metrics['total_predicted_vessels']} vessels")
    print(f"True Positives:    {metrics['true_positives']} | Missed: {metrics['missed_detections']}")
    print(f"Saved metrics:     {metrics_file}")
    print("=" * 65)

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/weights/vhrv_best.pt")
    parser.add_argument("--data", default="data/vhrv/vhrv/vhrv.yaml")
    parser.add_argument("--split", default="test")
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.60)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    evaluate_detector(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
    )
