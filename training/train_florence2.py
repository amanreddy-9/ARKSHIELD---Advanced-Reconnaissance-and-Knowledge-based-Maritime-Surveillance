import os
import json
import random
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from transformers import AutoProcessor, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_ID = "microsoft/Florence-2-base"

JSON_PATH = r".\data\TITANIC-FGS-10\Instruction_train\ship_data_10class.json"
IMAGE_ROOT = r".\data\TITANIC-FGS\TITANIC-FGS\Instruction_train"

OUTPUT_DIR = r".\models\weights\florence2_lora_test"

TRAIN_SAMPLES = 1000
VAL_SAMPLES = 200

EPOCHS = 2
BATCH_SIZE = 1
GRAD_ACCUMULATION = 4

MAX_TARGET_LENGTH = 128

SEED = 42


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# DEVICE
# ============================================================

device = "cuda" if torch.cuda.is_available() else "cpu"

print("=" * 60)
print("FLORENCE-2 LoRA FEASIBILITY TRAINING")
print("=" * 60)

print("Device:", device)

if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))
    print(
        "GPU Memory:",
        round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2),
        "GB"
    )


# ============================================================
# DATASET
# ============================================================

class FlorenceDataset(Dataset):

    def __init__(self, records, processor):
        self.records = records
        self.processor = processor

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):

        record = self.records[index]

        image_path = os.path.join(
            IMAGE_ROOT,
            record["path"].replace("/", os.sep)
        )

        image = Image.open(image_path).convert("RGB")

        conversations = record["conversations"]

        # Last human question
        question = None
        answer = None

        for i in range(len(conversations) - 1):
            if (
                conversations[i]["from"] == "human"
                and conversations[i + 1]["from"] == "gpt"
            ):
                question = conversations[i]["value"]
                answer = conversations[i + 1]["value"]

        if question is None or answer is None:
            raise ValueError("Could not find question/answer pair")

        question = question.replace("<image>", "").strip()

        # Florence-2 VQA task
        prompt = "<VQA> " + question

        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )

        target = self.processor.tokenizer(
            answer,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=MAX_TARGET_LENGTH
        )

        labels = target.input_ids

        labels[labels == self.processor.tokenizer.pad_token_id] = -100

        # Remove batch dimension
        inputs = {
            key: value.squeeze(0)
            for key, value in inputs.items()
            if torch.is_tensor(value)
        }

        labels = labels.squeeze(0)

        inputs["labels"] = labels

        return inputs


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading instruction dataset...")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    all_records = json.load(f)

print("Total records:", len(all_records))


# ============================================================
# BALANCED SMALL FEASIBILITY SAMPLE
# ============================================================

classes = [
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


grouped = {c: [] for c in classes}

for record in all_records:

    filename = record["image"]

    for class_name in classes:

        if filename.startswith(class_name + "_"):
            grouped[class_name].append(record)
            break


train_records = []
val_records = []

train_per_class = TRAIN_SAMPLES // len(classes)
val_per_class = VAL_SAMPLES // len(classes)

for class_name in classes:

    records = grouped[class_name].copy()

    random.shuffle(records)

    val_part = records[:val_per_class]
    train_part = records[
        val_per_class:
        val_per_class + train_per_class
    ]

    train_records.extend(train_part)
    val_records.extend(val_part)


random.shuffle(train_records)
random.shuffle(val_records)

print("\nTraining samples:", len(train_records))
print("Validation samples:", len(val_records))

print("\nSamples per class:")

for class_name in classes:

    train_count = sum(
        1
        for r in train_records
        if r["image"].startswith(class_name + "_")
    )

    val_count = sum(
        1
        for r in val_records
        if r["image"].startswith(class_name + "_")
    )

    print(
        f"{class_name:30s} "
        f"train={train_count} "
        f"val={val_count}"
    )


# ============================================================
# LOAD FLORENCE-2
# ============================================================

print("\nLoading Florence-2...")

processor = AutoProcessor.from_pretrained(
    MODEL_ID,
    trust_remote_code=True
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    attn_implementation="eager",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)

model = model.to(device)

model.config.use_cache = False


# ============================================================
# FIND LANGUAGE MODEL LINEAR LAYERS
# ============================================================

print("\nFinding LoRA target layers...")

target_modules = []

for name, module in model.named_modules():

    if not name.startswith("language_model"):
        continue

    if not isinstance(module, torch.nn.Linear):
        continue

    if name.endswith(("q_proj", "v_proj")):
        target_modules.append(name)


if len(target_modules) == 0:

    print("No q_proj/v_proj layers found.")

    for name, module in model.named_modules():

        if (
            name.startswith("language_model")
            and isinstance(module, torch.nn.Linear)
            and name.endswith(("q_proj", "k_proj", "v_proj", "out_proj"))
        ):
            target_modules.append(name)


if len(target_modules) == 0:
    raise RuntimeError("Could not find suitable LoRA target modules.")


print("LoRA target layers:", len(target_modules))

for name in target_modules[:10]:
    print(" ", name)


# ============================================================
# APPLY LoRA
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
# DATA LOADERS
# ============================================================

train_dataset = FlorenceDataset(
    train_records,
    processor
)

val_dataset = FlorenceDataset(
    val_records,
    processor
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
    lr=1e-4,
    weight_decay=0.01
)


# ============================================================
# TRAINING
# ============================================================

print("\nStarting training...")
print("=" * 60)

model.train()

if device == "cuda":

    scaler = torch.amp.GradScaler("cuda")

else:

    scaler = None


global_step = 0

for epoch in range(EPOCHS):

    print(f"\nEpoch {epoch + 1}/{EPOCHS}")

    optimizer.zero_grad()

    total_loss = 0.0

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

                loss = outputs.loss / GRAD_ACCUMULATION

            scaler.scale(loss).backward()

        else:

            outputs = model(**batch)

            loss = outputs.loss / GRAD_ACCUMULATION

            loss.backward()


        total_loss += loss.item() * GRAD_ACCUMULATION

        if (step + 1) % GRAD_ACCUMULATION == 0:

            if device == "cuda":

                scaler.step(optimizer)
                scaler.update()

            else:

                optimizer.step()

            optimizer.zero_grad()

            global_step += 1

        if (step + 1) % 10 == 0:

            print(
                f"Step {step + 1}/{len(train_loader)} "
                f"Loss: {total_loss / (step + 1):.4f}"
            )


# ============================================================
# VALIDATION
# ============================================================

print("\nRunning validation...")

model.eval()

val_loss = 0.0

with torch.no_grad():

    for batch in val_loader:

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

        val_loss += outputs.loss.item()


average_val_loss = val_loss / len(val_loader)

print("\nValidation loss:", round(average_val_loss, 4))


# ============================================================
# SAVE
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

model.save_pretrained(OUTPUT_DIR)
processor.save_pretrained(OUTPUT_DIR)

print("\nLoRA adapter saved to:")
print(OUTPUT_DIR)


# ============================================================
# GPU MEMORY
# ============================================================

if device == "cuda":

    peak_memory = (
        torch.cuda.max_memory_allocated() / 1024**3
    )

    print(
        "\nPeak GPU memory:",
        round(peak_memory, 2),
        "GB"
    )


print("\n" + "=" * 60)
print("FLORENCE-2 FEASIBILITY TEST COMPLETE")
print("=" * 60)