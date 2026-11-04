import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM


class Florence2VLM:
    def __init__(self, model_id="microsoft/Florence-2-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Loading Florence-2 on {self.device}...")

        self.processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            attn_implementation="eager"
        ).to(self.device)

        self.model.eval()

        print("Florence-2 loaded successfully.")
        if self.device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")

    def generate(self, image_path, task="<CAPTION>", max_new_tokens=100):
        image = Image.open(image_path).convert("RGB")

        inputs = self.processor(
            text=task,
            images=image,
            return_tensors="pt"
        )

        inputs = {
            k: v.to(self.device) if hasattr(v, "to") else v
            for k, v in inputs.items()
        }

        with torch.no_grad():
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=max_new_tokens,
                num_beams=1,
                use_cache=False
            )

        result = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=False
        )[0]

        return result


if __name__ == "__main__":
    image_path = (
        r".\data\TITANIC-FGS\TITANIC-FGS\ImageNet"
        r"\test\Aircraft_carrier\Test_Aircraft_carrier_0.jpg"
    )

    vlm = Florence2VLM()

    output = vlm.generate(
        image_path,
        task="<CAPTION>"
    )

    print("\nFLORENCE-2 OUTPUT:")
    print(output)