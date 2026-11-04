"""
training/inspect_vhrv_labels.py
VHRV Dataset Label Inspection and Ground Truth Verification Diagnostic
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def inspect_labels(data_root="data/vhrv/vhrv", output_dir="outputs/diagnostics"):
    data_root = Path(data_root)
    output_dir = Path(output_dir)
    samples_dir = output_dir / "ground_truth_samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    summary = {}
    splits = ["train", "val", "test"]

    for split in splits:
        img_dir = data_root / "images" / split
        lbl_dir = data_root / "labels" / split

        img_files = sorted(list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")))
        lbl_files = sorted(list(lbl_dir.glob("*.txt")))

        total_instances = 0
        box_widths = []
        box_heights = []
        aspect_ratios = []
        classes = set()
        out_of_bounds = 0
        empty_images = 0
        images_with_ships = 0
        instances_per_image = []

        for img_p in img_files:
            lbl_p = lbl_dir / (img_p.stem + ".txt")
            if not lbl_p.exists():
                empty_images += 1
                instances_per_image.append(0)
                continue

            with open(lbl_p, "r", encoding="utf-8") as f:
                lines = [l.strip().split() for l in f if l.strip()]

            cnt = len(lines)
            if cnt == 0:
                empty_images += 1
            else:
                images_with_ships += 1
            instances_per_image.append(cnt)
            total_instances += cnt

            for parts in lines:
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    classes.add(cls_id)
                    cx, cy, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    x1 = cx - w / 2.0
                    y1 = cy - h / 2.0
                    x2 = cx + w / 2.0
                    y2 = cy + h / 2.0

                    if x1 < 0.0 or y1 < 0.0 or x2 > 1.0 or y2 > 1.0 or w <= 0 or h <= 0:
                        out_of_bounds += 1

                    box_widths.append(w)
                    box_heights.append(h)
                    aspect_ratios.append(w / max(1e-6, h))

        summary[split] = {
            "image_count": len(img_files),
            "label_count": len(lbl_files),
            "total_instances": total_instances,
            "images_with_vessels": images_with_ships,
            "empty_background_images": empty_images,
            "avg_instances_per_image": round(float(np.mean(instances_per_image)), 2) if instances_per_image else 0,
            "max_instances_in_single_image": int(max(instances_per_image)) if instances_per_image else 0,
            "classes_detected": list(classes),
            "out_of_bounds_boxes": out_of_bounds,
            "norm_width": {
                "min": round(float(min(box_widths)), 4) if box_widths else 0,
                "max": round(float(max(box_widths)), 4) if box_widths else 0,
                "mean": round(float(np.mean(box_widths)), 4) if box_widths else 0,
            },
            "norm_height": {
                "min": round(float(min(box_heights)), 4) if box_heights else 0,
                "max": round(float(max(box_heights)), 4) if box_heights else 0,
                "mean": round(float(np.mean(box_heights)), 4) if box_heights else 0,
            },
            "aspect_ratio": {
                "min": round(float(min(aspect_ratios)), 2) if aspect_ratios else 0,
                "max": round(float(max(aspect_ratios)), 2) if aspect_ratios else 0,
                "mean": round(float(np.mean(aspect_ratios)), 2) if aspect_ratios else 0,
            },
        }

        # Save visual ground truth samples for test split
        if split == "test":
            sample_stems = ["vhrv_00038", "vhrv_00050", "vhrv_00113", "vhrv_01045", "vhrv_01229"]
            for stem in sample_stems:
                s_img_p = img_dir / f"{stem}.jpg"
                s_lbl_p = lbl_dir / f"{stem}.txt"
                if not s_img_p.exists() or not s_lbl_p.exists():
                    continue

                with Image.open(s_img_p) as im:
                    draw_im = im.copy().convert("RGB")
                draw = ImageDraw.Draw(draw_im)
                W, H = draw_im.size

                with open(s_lbl_p, "r", encoding="utf-8") as f:
                    for line in f:
                        p = line.strip().split()
                        if len(p) >= 5:
                            cx, cy, w, h = float(p[1]) * W, float(p[2]) * H, float(p[3]) * W, float(p[4]) * H
                            x1, y1 = cx - w / 2.0, cy - h / 2.0
                            x2, y2 = cx + w / 2.0, cy + h / 2.0
                            # Green neutral box for ground truth
                            draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=4)

                # Resize to manageable preview size while preserving aspect ratio
                preview_w = 1600
                preview_h = int(H * (preview_w / W))
                draw_im = draw_im.resize((preview_w, preview_h), Image.Resampling.LANCZOS)
                draw_im.save(samples_dir / f"gt_{stem}.jpg", quality=92)

    # Save summary report
    report_p = output_dir / "vhrv_label_inspection.json"
    with open(report_p, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("VHRV DATASET INSPECTION REPORT")
    print("=" * 60)
    for split, s in summary.items():
        print(f"\n--- {split.upper()} SPLIT ---")
        print(f"Images: {s['image_count']} | Labels: {s['label_count']} | Instances: {s['total_instances']}")
        print(f"Avg Ships/Img: {s['avg_instances_per_image']} | Max Ships in single image: {s['max_instances_in_single_image']}")
        print(f"Out of Bounds: {s['out_of_bounds_boxes']} | Classes: {s['classes_detected']}")
        print(f"Width (norm): min={s['norm_width']['min']}, max={s['norm_width']['max']}, mean={s['norm_width']['mean']}")
        print(f"Height (norm): min={s['norm_height']['min']}, max={s['norm_height']['max']}, mean={s['norm_height']['mean']}")
    print(f"\nSaved JSON report: {report_p}")
    print(f"Saved visual ground truth samples to: {samples_dir}")
    return summary


if __name__ == "__main__":
    inspect_labels()
