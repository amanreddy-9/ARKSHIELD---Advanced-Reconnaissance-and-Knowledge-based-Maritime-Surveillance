import torch
from PIL import Image
from pathlib import Path
import numpy as np
from torchvision import models, transforms


class ShipClassifier:
    CLASS_NAMES = [
        "Aircraft carrier",
        "Amphibious assault ship",
        "Cruise ship",
        "Cruiser",
        "Destroyer",
        "Frigate",
        "Littoral combat ship",
        "Non ship",
        "Oil tanker",
        "Yacht",
    ]

    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model = models.convnext_tiny(weights=None)

        self.model.classifier[2] = torch.nn.Linear(
            self.model.classifier[2].in_features,
            len(self.CLASS_NAMES)
        )

        checkpoint = torch.load(
            Path(__file__).resolve().parent / "weights/convnext_tiny/best.pt",
            map_location=self.device
        )

        # Training saves ImageFolder ordering; always honor checkpoint metadata.
        saved_classes = checkpoint.get("class_names") if isinstance(checkpoint, dict) else None
        if saved_classes:
            if len(saved_classes) != len(self.CLASS_NAMES):
                raise ValueError("Classifier checkpoint class count mismatch")
            self.CLASS_NAMES = [name.replace("_", " ") for name in saved_classes]

        # Support both a raw state_dict and a training checkpoint
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        else:
            state_dict = checkpoint

        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

    def classify(self, crop, vlm=None, use_vlm_disambiguation=True):
        """
        Classify a cropped ship image with ConvNeXt-Tiny backbone and
        intelligent Multimodal VLM disambiguation for close combatant classes.

        crop can be:
        - a PIL Image
        - a numpy image
        """
        if not isinstance(crop, Image.Image):
            import cv2
            if not isinstance(crop, np.ndarray) or crop.ndim != 3 or crop.shape[2] != 3 or not crop.size:
                raise ValueError("Expected non-empty BGR image or RGB PIL image")
            crop = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        if crop.width < 1 or crop.height < 1:
            raise ValueError("Empty vessel crop")

        crop_rgb = crop.convert("RGB")
        image = self.transform(crop_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(image)
            probabilities = torch.softmax(logits, dim=1)[0]
            confidence, class_id = torch.max(probabilities, dim=0)

        raw_label = self.CLASS_NAMES[class_id.item()]
        raw_conf = float(confidence.item())

        # Check top-2 candidates to detect close combatant ambiguity
        probs_np = probabilities.cpu().numpy()
        ranked = sorted(zip(self.CLASS_NAMES, probs_np), key=lambda x: x[1], reverse=True)
        top1_name, top1_prob = ranked[0]
        top2_name, top2_prob = ranked[1]
        margin = top1_prob - top2_prob

        # Ambiguity condition: naval combatants or low margin
        combatants = {"Destroyer", "Frigate", "Cruiser", "Littoral combat ship"}
        is_combatant_contest = (top1_name in combatants and (top2_name in combatants or top1_prob < 0.85))
        is_close_call = margin < 0.25

        if use_vlm_disambiguation and (is_combatant_contest or is_close_call):
            if vlm is not None:
                try:
                    vlm_res = vlm.classify_vessel(crop_rgb)
                    if vlm_res and vlm_res.get("label") in self.CLASS_NAMES:
                        return {
                            "label": vlm_res["label"],
                            "confidence": round(float(vlm_res.get("confidence", 0.95)), 4),
                            "reasoning": vlm_res.get("reasoning", ""),
                            "model": "ConvNeXt-Tiny + Groq-VLM Disambiguation",
                            "vlm_reasoned": True,
                            "raw_convnext_label": raw_label,
                            "raw_convnext_conf": round(raw_conf, 4),
                        }
                except Exception as e:
                    print(f"[WARN] VLM disambiguation fallback: {e}")

        return {
            "label": raw_label,
            "confidence": round(raw_conf, 4),
            "model": "ConvNeXt-Tiny",
            "vlm_reasoned": False,
            "probabilities": {name: float(prob) for name, prob in ranked},
            "candidates": [{"label": name, "confidence": float(prob)} for name, prob in ranked[:2]],
            "margin": float(margin),
            "uncertain": bool(margin < 0.25 or raw_conf < 0.55),
        }