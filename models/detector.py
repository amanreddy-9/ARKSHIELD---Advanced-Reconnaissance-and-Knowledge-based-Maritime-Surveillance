# models/detector.py
"""
Dual-Domain Vessel Detector for OATrack-VLM.
Supports:
1. Satellite Mode: High-resolution (imgsz=1024) detection on wide optical satellite imagery (VHRV)
   using fine-tuned YOLO11n weights.
2. Drone Mode: Full-hull vessel detection on tactical aerial/drone surveillance feeds,
   ensuring the bounding box encloses the entire vessel (bow-to-stern, deck-to-waterline)
   rather than isolated deck fittings or parked planes.
"""

from pathlib import Path
import os
import numpy as np
from PIL import Image

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None


BASE_DIR = Path(__file__).resolve().parents[1]


class ModelLoadError(RuntimeError):
    """Selected detector weights could not be read or loaded."""


def project_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


class VesselDetector:
    """
    Intelligent Dual-Domain Vessel Detector.
    Routes inference to the appropriate specialized model depending on observation modality:
      - 'satellite': High-res VHRV model (imgsz=1024)
      - 'drone': Full-vessel aerial model (classes=[8] boat)
    """

    def __init__(self, weights_path=None, drone_weights="yolo11n.pt"):
        default_satellite_weights = "models/weights/vhrv_best.pt"
        self.satellite_weights = weights_path or os.getenv("VHRV_MODEL_PATH", default_satellite_weights)
        self.drone_weights = drone_weights
        
        self.conf = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
        self.iou = float(os.getenv("IOU_THRESHOLD", "0.60"))
        self.drone_conf = 0.18
        self.drone_iou = 0.45

        self.satellite_model = None
        self.drone_model = None
        self.model = None  # Compatibility alias
        
        self.load_models()

    def load_models(self):
        """Load both satellite and drone vessel models."""
        if YOLO is None:
            return

        # 1. Satellite Model (VHRV)
        sat_p = project_path(self.satellite_weights)
        if sat_p.exists():
            try:
                self.satellite_model = YOLO(str(sat_p))
                self.model = self.satellite_model  # Backwards compatibility
                self.is_custom = "custom" in sat_p.name.lower()
                self.model_name = "Custom Maritime YOLO" if self.is_custom else "YOLO11n-VHRV Baseline"
            except Exception as e:
                print(f"[WARN] Failed to load satellite model {sat_p}: {e}")

        # 2. Drone Aerial Full-Vessel Model
        try:
            drone_p = project_path(self.drone_weights)
            # If not in current dir, ultralytics will auto-download or find cached yolo11n.pt
            self.drone_model = YOLO(str(drone_p))
        except Exception as e:
            print(f"[WARN] Failed to load drone model {self.drone_weights}: {e}")
            self.drone_model = self.satellite_model

    def load_model(self, weights_path):
        """Load selected weights relative to the project, independent of shell cwd."""
        raw_str = str(weights_path).strip()
        if "custom" in raw_str.lower():
            resolved = project_path("models/weights/vhrv_custom_best.pt")
        else:
            resolved = project_path("models/weights/vhrv_best.pt")
        key = str(resolved)
        if not hasattr(self, "_cached_models"):
            self._cached_models = {}
            if self.satellite_model is not None:
                self._cached_models[str(project_path(self.satellite_weights))] = self.satellite_model
        try:
            if key in self._cached_models:
                new_model = self._cached_models[key]
            else:
                if YOLO is None:
                    raise ModelLoadError("YOLO is unavailable. Check the ultralytics installation.")
                if not resolved.is_file():
                    raise ModelLoadError(f"Selected model weights are missing: {resolved}")
                new_model = YOLO(key)
                self._cached_models[key] = new_model
        except ModelLoadError:
            raise
        except Exception as exc:
            raise ModelLoadError(
                f"Could not load selected model weights: {resolved}. "
                f"Check that the drive is connected and the file is readable. ({exc})"
            ) from exc
        self.satellite_model = new_model
        self.satellite_weights = key
        self.model = new_model
        self.is_custom = "custom" in resolved.name.lower()
        self.model_name = "Custom Maritime YOLO" if self.is_custom else "YOLO11n-VHRV Baseline"

    def predict(self, image_source, mode="auto", conf=None, iou=None, imgsz=None, max_det=500):
        """
        Run vessel detection on an image path, PIL image, or numpy array.

        Parameters:
            image_source: filepath, PIL Image, or numpy array
            mode: 'satellite', 'drone', or 'auto'
            conf: confidence threshold override
            iou: NMS IoU threshold override
            imgsz: inference resolution override
            max_det: maximum detections per frame

        Returns:
            list of standardized detection dictionaries
        """
        # Determine observation domain
        if mode == "auto":
            is_satellite = False
            if isinstance(image_source, (str, Path)):
                try:
                    with Image.open(image_source) as im:
                        w, h = im.size
                        is_satellite = max(w, h) >= 1800
                except Exception:
                    is_satellite = False
            elif hasattr(image_source, "shape"):
                h, w = image_source.shape[:2]
                is_satellite = max(w, h) >= 1800
            target_mode = "satellite" if is_satellite else "drone"
        else:
            target_mode = mode.lower()

        if target_mode == "drone":
            return self._predict_drone(image_source, conf=conf, iou=iou, imgsz=imgsz, max_det=max_det)
        else:
            return self._predict_satellite(image_source, conf=conf, iou=iou, imgsz=imgsz, max_det=max_det)

    def _predict_satellite(self, image_source, conf=None, iou=None, imgsz=None, max_det=500):
        """High-resolution satellite vessel detection with VHRV model."""
        model = self.satellite_model or self.model
        if model is None:
            return []

        c_thresh = conf if conf is not None else self.conf
        iou_thresh = iou if iou is not None else self.iou
        eval_imgsz = imgsz if imgsz is not None else 1024

        results = model.predict(
            source=image_source,
            conf=c_thresh,
            iou=iou_thresh,
            imgsz=eval_imgsz,
            max_det=max_det,
            verbose=False,
        )

        detections = []
        for result in results:
            names = result.names
            if getattr(result, "boxes", None) is not None:
                for box in result.boxes:
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    bbox = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = bbox
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    width = x2 - x1
                    height = y2 - y1

                    detections.append({
                        "class_id": class_id,
                        "class_name": names.get(class_id, "vessel"),
                        "confidence": round(confidence, 4),
                        "bbox": [round(c, 2) for c in bbox],
                        "cx": round(cx, 2),
                        "cy": round(cy, 2),
                        "w": round(width, 2),
                        "h": round(height, 2),
                        "angle": 0.0,
                    })
        return detections

    def _predict_drone(self, image_source, conf=None, iou=None, imgsz=None, max_det=500):
        """
        Drone aerial vessel detection.
        Detects full vessel hulls (boat class 8), suppressing partial internal fragments
        so that bounding boxes cover the ENTIRE ship from bow to stern.
        """
        model = self.drone_model or self.satellite_model
        if model is None:
            return []

        c_thresh = conf if conf is not None else self.drone_conf
        iou_thresh = iou if iou is not None else self.drone_iou
        eval_imgsz = imgsz if imgsz is not None else 640

        results = model.predict(
            source=image_source,
            conf=c_thresh,
            iou=iou_thresh,
            classes=[8],  # COCO class 8: 'boat'
            imgsz=eval_imgsz,
            max_det=max_det,
            verbose=False,
        )

        raw_boats = []
        for result in results:
            if getattr(result, "boxes", None) is not None:
                for box in result.boxes:
                    confidence = float(box.conf.item())
                    bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                    bw = max(1.0, bx2 - bx1)
                    bh = max(1.0, by2 - by1)
                    raw_boats.append({
                        "bbox": [bx1, by1, bx2, by2],
                        "confidence": confidence,
                        "cx": (bx1 + bx2) / 2.0,
                        "cy": (by1 + by2) / 2.0,
                        "w": bw,
                        "h": bh,
                        "area": bw * bh,
                        "class_id": 0,
                        "class_name": "vessel",
                    })

        # Sort largest vessel area first to ensure full-hull envelopes dominate
        raw_boats.sort(key=lambda x: x["area"], reverse=True)

        # Suppress sub-parts: if box A's center is inside a larger boat B or overlaps heavily,
        # it is an internal deck fitting or cabin â€” suppress it into the whole ship!
        filtered_boats = []
        for boat in raw_boats:
            bx1, by1, bx2, by2 = boat["bbox"]
            bcx, bcy = boat["cx"], boat["cy"]
            is_subpart = False

            for parent in filtered_boats:
                px1, py1, px2, py2 = parent["bbox"]
                # Check if boat center lies inside parent box
                center_inside = (px1 <= bcx <= px2) and (py1 <= bcy <= py2)
                
                # Check IoU with parent
                ix1 = max(bx1, px1)
                iy1 = max(by1, py1)
                ix2 = min(bx2, px2)
                iy2 = min(by2, py2)
                inter_area = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
                overlap_ratio = inter_area / max(1.0, boat["area"])

                # Containment is evidence of a subpart only when much smaller.
                # Do not expand the accepted hull with an untrusted proposal.
                if center_inside and overlap_ratio >= 0.60 and boat["area"] < .65*parent["area"]:
                    is_subpart = True
                    break

            if not is_subpart:
                filtered_boats.append(boat)

        # Standardize return structure
        detections = []
        for b in filtered_boats:
            detections.append({
                "class_id": 0,
                "class_name": "vessel",
                "confidence": round(b["confidence"], 4),
                "bbox": [round(c, 2) for c in b["bbox"]],
                "cx": round(b["cx"], 2),
                "cy": round(b["cy"], 2),
                "w": round(b["w"], 2),
                "h": round(b["h"], 2),
                "angle": 0.0,
            })

        return detections

    def crop(self, image_input, bbox):
        """
        Crop a detected vessel.
        When the bounding box is already the full vessel hull, applies a small
        clean 5% margin to preserve context without clipping vessel extremities.
        """
        if isinstance(image_input, (str, Path)):
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        elif hasattr(image_input, "shape"):
            import cv2
            image = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
        else:
            image = Image.fromarray(image_input).convert("RGB")

        x1, y1, x2, y2 = map(float, bbox)
        if not np.isfinite([x1,y1,x2,y2]).all() or x2<=x1 or y2<=y1:
            raise ValueError("Invalid vessel crop box")
        if min(image.width,x2)<=max(0,x1) or min(image.height,y2)<=max(0,y1):
            raise ValueError("Vessel crop lies outside image")
        box_w = max(1.0, x2 - x1)
        box_h = max(1.0, y2 - y1)

        # Clean 5% context padding around the vessel
        pad_x = box_w * 0.05
        pad_y = box_h * 0.05

        x1 = max(0, int(x1 - pad_x))
        y1 = max(0, int(y1 - pad_y))
        x2 = min(image.width, int(x2 + pad_x))
        y2 = min(image.height, int(y2 + pad_y))

        # Ensure minimum dimensions
        if (x2 - x1) < 32 or (y2 - y1) < 32:
            x1 = max(0, int(x1 - 16))
            y1 = max(0, int(y1 - 16))
            x2 = min(image.width, int(x2 + 16))
            y2 = min(image.height, int(y2 + 16))

        return image.crop((x1, y1, x2, y2))