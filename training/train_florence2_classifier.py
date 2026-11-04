import os
import random
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from transformers import AutoProcessor, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model


# ============================================================
# CONFIG
# ============================================================

MODEL_ID = "microsoft/Florence-2-base"

TRAIN_ROOT = r".\data\TITANIC-FGS-10\ImageNet\train"
VAL_ROOT = r".\data\TITANIC-FGS-10\ImageNet\val"

OUTPUT_DIR = r".\models\weights\florence2_classifier_lora"

EPOCHS = 5
BATCH_SIZE = 1
GRAD_ACCUMULATION = 4

MAX_TARGET_LENGTH = 32

LR = 1e-4
SEED = 42


# ============================================================
# CLASSES
# ============================================================

CLASSES = [
    "Aircraft_carrier",
    "Amphibious_assault_ship",
    "Cruiser",
    "Destroyer",
    "Frigate",
    "Littoral_combat_ship",
    "Cruise_ship",
    "Oil_tanker",
    "Yacht",
    "Non_ship",
]


DISPLAY_NAMES = {
    "Aircraft_carrier": "Aircraft carrier",
    "Amphibious_assault_ship": "Amphibious assault ship",
    "Cruiser": "Cruiser",
    "Destroyer": "Destroyer",
    "Frigate": "Frigate",
    "Littoral_combat_ship": "Littoral combat ship",
    "Cruise_ship": "Cruise ship",
    "Oil_tanker": "Oil tanker",
    "Yacht": "Yacht",
    "Non_ship": "Non ship",
}


# ============================================================
# SEED
# ============================================================

random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# DEVICE
# ============================================================

device = "cuda" if torch.cuda.is_available() else "cpu"

print("=" * 70)
print("FLORENCE-2 BALANCED 10-CLASS CLASSIFIER")
print("=" * 70)

print("Device:", device)

if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))
    print(
        "VRAM:",
        round(
            torch.cuda.get_device_properties(0).total_memory / 1024**3,
            2
        ),
        "GB"
    )


# ============================================================
# DATASET
# ============================================================

class ShipDataset(Dataset):

    def __init__(self, root, processor):

        self.processor = processor
        self.samples = []

        for class_name in CLASSES:

            class_dir = os.path.join(
                root,
                class_name
            )

            if not os.path.isdir(class_dir):
                raise FileNotFoundError(
                    f"Missing directory: {class_dir}"
                )

            for filename in os.listdir(class_dir):

                if filename.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".bmp", ".webp")
                ):

                    self.samples.append(
                        (
                            os.path.join(
                                class_dir,
                                filename
                            ),
                            class_name
                        )
                    )

        random.shuffle(self.samples)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):

        image_path, class_name = self.samples[index]

        image = Image.open(
            image_path
        ).convert("RGB")

        # Strict classification prompt
        prompt = (
            "<VQA> "
            "What is the fine-grained type of ship in this image? "
            "Answer with only the class name."
        )

        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )

        target = self.processor.tokenizer(
            DISPLAY_NAMES[class_name],
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=MAX_TARGET_LENGTH
        )

        labels = target.input_ids

        labels[
            labels == self.processor.tokenizer.pad_token_id
        ] = -100

        inputs = {
            key: value.squeeze(0)
            for key, value in inputs.items()
            if torch.is_tensor(value)
        }

        inputs["labels"] = labels.squeeze(0)

        return inputs


# ============================================================
# LOAD PROCESSOR
# ============================================================

print("\nLoading processor...")

processor = AutoProcessor.from_pretrained(
    MODEL_ID,
    trust_remote_code=True
)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading Florence-2...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    attn_implementation="eager",
    torch_dtype=(
        torch.float16
        if device == "cuda"
        else torch.float32
    )
)

model = model.to(device)

model.config.use_cache = False


# ============================================================
# FIND LoRA TARGETS
# ============================================================

print("\nFinding LoRA layers...")

target_modules = []

for name, module in model.named_modules():

    if not name.startswith("language_model"):
        continue

    if not isinstance(module, torch.nn.Linear):
        continue

    if name.endswith(("q_proj", "v_proj")):
        target_modules.append(name)


if not target_modules:

    for name, module in model.named_modules():

        if not name.startswith("language_model"):
            continue

        if not isinstance(module, torch.nn.Linear):
            continue

        if name.endswith(
            ("q_proj", "k_proj", "v_proj", "out_proj")
        ):
            target_modules.append(name)


if not target_modules:
    raise RuntimeError(
        "Could not find LoRA target layers."
    )

print(
    "LoRA target layers:",
    len(target_modules)
)


# ============================================================
# LoRA
# ============================================================

print("\nApplying LoRA...")

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type="SEQ_2_SEQ_LM",
    target_modules=target_modules
)

model = get_peft_model(
    model,
    lora_config
)

model.print_trainable_parameters()


# ============================================================
# DATA
# ============================================================

print("\nLoading training dataset...")

train_dataset = ShipDataset(
    TRAIN_ROOT,
    processor
)

print(
    "Training images:",
    len(train_dataset)
)

print("\nLoading validation dataset...")

val_dataset = ShipDataset(
    VAL_ROOT,
    processor
)

print(
    "Validation images:",
    len(val_dataset)
)


train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# OPTIMIZER
# ============================================================

trainable_params = [
    p
    for p in model.parameters()
    if p.requires_grad
]

optimizer = torch.optim.AdamW(
    trainable_params,
    lr=LR,
    weight_decay=0.01
)


# ============================================================
# TRAIN
# ============================================================

print("\nStarting training...")
print("=" * 70)

model.train()

if device == "cuda":

    scaler = torch.amp.GradScaler("cuda")

else:

    scaler = None


for epoch in range(EPOCHS):

    print(
        f"\nEpoch {epoch + 1}/{EPOCHS}"
    )

    optimizer.zero_grad()

    running_loss = 0.0

    for step, batch in enumerate(train_loader):

        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        if device == "cuda":

            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16
            ):

                outputs = model(**batch)

                loss = (
                    outputs.loss /
                    GRAD_ACCUMULATION
                )

            scaler.scale(loss).backward()

        else:

            outputs = model(**batch)

            loss = (
                outputs.loss /
                GRAD_ACCUMULATION
            )

            loss.backward()

        running_loss += (
            loss.item() *
            GRAD_ACCUMULATION
        )

        if (
            (step + 1) %
            GRAD_ACCUMULATION
            == 0
        ):

            if device == "cuda":

                scaler.step(optimizer)
                scaler.update()

            else:

                optimizer.step()

            optimizer.zero_grad()

        if (step + 1) % 100 == 0:

            avg_loss = (
                running_loss /
                (step + 1)
            )

            print(
                f"Step {step + 1}/{len(train_loader)} "
                f"Loss: {avg_loss:.4f}"
            )


# ============================================================
# VALIDATION LOSS
# ============================================================

print("\nRunning validation...")

model.eval()

total_val_loss = 0.0

with torch.no_grad():

    for step, batch in enumerate(val_loader):

        batch = {
            key: value.to(device)
            for key, value in batch.items()
        }

        if device == "cuda":

            with torch.autocast(
                device_type="cuda",
                dtype=torch.float16
            ):

                outputs = model(**batch)

        else:

            outputs = model(**batch)

        total_val_loss += outputs.loss.item()

        if (step + 1) % 100 == 0:

            print(
                f"Validation: "
                f"{step + 1}/{len(val_loader)}"
            )


val_loss = (
    total_val_loss /
    len(val_loader)
)

print(
    "\nValidation loss:",
    round(val_loss, 4)
)


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

model.save_pretrained(
    OUTPUT_DIR
)

processor.save_pretrained(
    OUTPUT_DIR
)

print("\nAdapter saved to:")
print(OUTPUT_DIR)


# ============================================================
# GPU MEMORY
# ============================================================

if device == "cuda":

    peak = (
        torch.cuda.max_memory_allocated()
        / 1024**3
    )

    print(
        "\nPeak GPU memory:",
        round(peak, 2),
        "GB"
    )


print("\n" + "=" * 70)
print("FLORENCE-2 CLASSIFIER TRAINING COMPLETE")
print("=" * 70)