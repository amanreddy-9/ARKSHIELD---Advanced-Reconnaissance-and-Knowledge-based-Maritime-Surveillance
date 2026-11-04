import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Load project .env file
load_dotenv()


class GroqVLM:
    def __init__(self):
        key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "")

        from models.vlm_guard import RequestGuard
        self.guard = RequestGuard.shared(self.model)

        self.client = (
            Groq(api_key=key, max_retries=0, timeout=20.0)
            if key
            else None
        )

    def generate_briefing(self, image_path, telemetry, mode="satellite"):
        if not self.client or not self.model:
            return {
                "status": "DISABLED",
                "text": "Configure GROQ_API_KEY and GROQ_MODEL in .env."
            }

        try:
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(
                    f.read()
                ).decode()

            prompt = (
                "Give a brief maritime image report grounded in this telemetry. "
                "Preserve target ordering and confidence; do not invent identity or motion. "
                + ("Static satellite image: no track IDs. " if mode == "satellite" else "Use exact track IDs and classifier labels. ")
                + "Separate observations from predictions. Telemetry: " + str(telemetry)[:4000]
            )

            response = self._request(
                model=self.model,
                max_tokens=int(os.getenv("GROQ_BRIEFING_MAX_TOKENS", "250")),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        "data:image/jpeg;base64,"
                                        + encoded
                                    )
                                },
                            },
                        ],
                    }
                ],
            )

            text = response.choices[0].message.content

            return {
                "source": self.guard.last_source,
                "status": "OK",
                "text": text,
            }

        except Exception as e:
            return {
                "status": "UNAVAILABLE",
                "availability": self.availability(),
                "text": "VLM unavailable; local detection remains available.",
            }

    def chat(self, user_message, chat_history=None, context_data=None):
        """
        Conversational assistant for maritime surveillance queries.
        """
        if not self.client or not self.model:
            return "Chatbot unavailable: GROQ_API_KEY is not configured in .env."

        system_prompt = (
            "You are the OATrack-VLM Maritime Surveillance AI Assistant.\n"
            "You assist surveillance operators with queries regarding vessel detections, "
            "drone tracks, classifications, scene complexity, and operational briefings.\n"
            "Answer concisely, professionally, and accurately using provided telemetry."
        )

        if context_data:
            system_prompt += f"\n\nCURRENT SURVEILLANCE CONTEXT:\n{str(context_data)[:2500]}\n"

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": str(msg.get("content", ""))[:1000]
                })

        messages.append({"role": "user", "content": str(user_message)[:2000]})

        try:
            resp = self._request(
                model=self.model,
                messages=messages,
                max_tokens=int(os.getenv("GROQ_CHAT_MAX_TOKENS", "300")),
                temperature=0.3,
            )
            return resp.choices[0].message.content
        except Exception as exc:
            return "Assistant temporarily unavailable. Please retry after the cooldown."

    def classify_vessel(self, image_source):
        """
        Multimodal fine-grained vessel classification using Groq Vision.
        Disambiguates visually challenging vessel classes (e.g. Frigate vs Destroyer)
        by reasoning over hull profile, pennant markings, mast and weapon systems.
        """
        if not self.client or not self.model:
            return None

        import io
        import json
        from PIL import Image
        import numpy as np

        try:
            # Prepare image as base64 JPEG
            if isinstance(image_source, (str, Path)):
                with open(image_source, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
            elif isinstance(image_source, Image.Image):
                buf = io.BytesIO()
                image_source.convert("RGB").save(buf, format="JPEG", quality=90)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
            elif isinstance(image_source, np.ndarray):
                import cv2
                # If OpenCV BGR array, convert to JPEG
                _, buf = cv2.imencode(".jpg", image_source)
                encoded = base64.b64encode(buf.tobytes()).decode("utf-8")
            else:
                return None

            valid_classes = [
                "Aircraft carrier", "Amphibious assault ship", "Cruise ship", "Cruiser",
                "Destroyer", "Frigate", "Littoral combat ship", "Non ship", "Oil tanker", "Yacht"
            ]

            prompt = (
                f"Classify this vessel as exactly one of {valid_classes}. "
                'Return JSON: {"label":str,"confidence":0..1,"reasoning":str}. '
                "Use visible evidence only; reasoning at most 25 words. Do not infer identity."
            )

            response = self._request(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                    ]
                }],
                temperature=0.1,
                max_tokens=int(os.getenv("GROQ_CLASSIFY_MAX_TOKENS", "120")),
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)
            label = parsed.get("label")
            # Normalize to match exact valid class
            matched_label = None
            for c in valid_classes:
                if label and c.lower() == label.lower():
                    matched_label = c
                    break
                elif label and c.lower() in label.lower():
                    matched_label = c

            if matched_label:
                import math
                confidence = float(parsed.get("confidence", 0.0))
                if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                    return None
                return {
                    "label": matched_label,
                    "confidence": confidence,
                    "reasoning": str(parsed.get("reasoning", ""))[:1000],
                    "model": f"Groq-VLM ({self.model})",
                }
            return None

        except Exception as e:
            pass  # The shared guard logs sanitized failure metadata once.
            return None
    def _request(self, **kwargs):
        if not self.client or not self.model:
            raise RuntimeError("VLM disabled")
        return self.guard.request(self.client, kwargs)

    def availability(self):
        return self.guard.snapshot(enabled=bool(self.client and self.model))
