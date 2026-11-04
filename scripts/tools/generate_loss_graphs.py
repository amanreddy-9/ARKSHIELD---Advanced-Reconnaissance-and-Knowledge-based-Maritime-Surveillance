"""
generate_loss_graphs.py
Generates publication-quality Training Loss vs. Validation Loss graphs
for both OATrack-VLM core models:
1. YOLO11n-VHRV Vessel Detector (60 epochs)
2. ConvNeXt-Tiny Fine-Grained Ship Classifier (5 epochs)

Saves all figures into outputs/ and outputs/loss_graphs/.
"""

import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set visual style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 1.0

outputs_dir = Path("outputs")
loss_graphs_dir = outputs_dir / "loss_graphs"
loss_graphs_dir.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 1. LOAD DATA
# ==============================================================================

# A. YOLO11n-VHRV Detector Data
yolo_csv_path = Path("runs/detect/runs/detect/vhrv_yolo11n_60ep2/results.csv")
if not yolo_csv_path.exists():
    raise FileNotFoundError(f"Missing YOLO results CSV at {yolo_csv_path}")

df_yolo = pd.read_csv(yolo_csv_path)
df_yolo.columns = [c.strip() for c in df_yolo.columns]

# Calculate total losses
df_yolo['train_total_loss'] = df_yolo['train/box_loss'] + df_yolo['train/cls_loss'] + df_yolo['train/dfl_loss']
df_yolo['val_total_loss'] = df_yolo['val/box_loss'] + df_yolo['val/cls_loss'] + df_yolo['val/dfl_loss']

# B. ConvNeXt-Tiny Classifier Data
convnext_json_path = Path("outputs/convnext_tiny/training_history.json")
if not convnext_json_path.exists():
    raise FileNotFoundError(f"Missing ConvNeXt history at {convnext_json_path}")

with open(convnext_json_path, "r") as f:
    convnext_data = json.load(f)

df_conv = pd.DataFrame(convnext_data)

# ==============================================================================
# 2. GENERATE GRAPH 1: YOLO11n-VHRV VESSEL DETECTOR LOSS & METRICS
# ==============================================================================
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), dpi=300)
fig.patch.set_facecolor('#0f172a')  # Sleek dark navy background

for ax in axes:
    ax.set_facecolor('#1e293b')
    ax.grid(True, linestyle='--', alpha=0.3, color='#94a3b8')
    ax.tick_params(colors='#e2e8f0', labelsize=10)
    for spine in ax.spines.values():
        spine.set_color('#334155')

# Panel 1: Total Train Loss vs Val Loss
ax1 = axes[0]
ax1.plot(df_yolo['epoch'], df_yolo['train_total_loss'], color='#38bdf8', linewidth=2.4, label='Training Total Loss', marker='o', markersize=3.5, alpha=0.9)
ax1.plot(df_yolo['epoch'], df_yolo['val_total_loss'], color='#f43f5e', linewidth=2.4, label='Validation Total Loss', marker='s', markersize=3.5, alpha=0.9)

# Mark minimum validation loss
min_val_idx = df_yolo['val_total_loss'].idxmin()
min_val_ep = df_yolo.loc[min_val_idx, 'epoch']
min_val_loss = df_yolo.loc[min_val_idx, 'val_total_loss']
ax1.scatter([min_val_ep], [min_val_loss], color='#fbbf24', s=120, zorder=5, edgecolor='#0f172a', linewidth=1.5)
ax1.annotate(
    f'Min Val Loss: {min_val_loss:.3f}\n(Epoch {int(min_val_ep)})',
    xy=(min_val_ep, min_val_loss),
    xytext=(min_val_ep + 4, min_val_loss + 0.35),
    color='#fbbf24',
    fontsize=9,
    fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='#fbbf24', lw=1.5)
)

ax1.set_title('YOLO11n: Total Train vs. Val Loss', fontsize=13, fontweight='bold', color='#f8fafc', pad=12)
ax1.set_xlabel('Training Epochs', fontsize=11, color='#cbd5e1')
ax1.set_ylabel('Total Objective Loss', fontsize=11, color='#cbd5e1')
ax1.legend(loc='upper right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)

# Panel 2: Component Breakdown (Box & Class Loss)
ax2 = axes[1]
ax2.plot(df_yolo['epoch'], df_yolo['train/box_loss'], color='#06b6d4', linestyle='-', linewidth=1.8, label='Train Box Loss')
ax2.plot(df_yolo['epoch'], df_yolo['val/box_loss'], color='#f97316', linestyle='--', linewidth=1.8, label='Val Box Loss')
ax2.plot(df_yolo['epoch'], df_yolo['train/cls_loss'], color='#a855f7', linestyle='-', linewidth=1.8, label='Train Cls Loss')
ax2.plot(df_yolo['epoch'], df_yolo['val/cls_loss'], color='#ec4899', linestyle='--', linewidth=1.8, label='Val Cls Loss')

ax2.set_title('Loss Component Breakdown (Box & Cls)', fontsize=13, fontweight='bold', color='#f8fafc', pad=12)
ax2.set_xlabel('Training Epochs', fontsize=11, color='#cbd5e1')
ax2.set_ylabel('Component Loss Value', fontsize=11, color='#cbd5e1')
ax2.legend(loc='upper right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=9.5)

# Panel 3: Validation Detection Accuracy (mAP@50 & mAP@50-95)
ax3 = axes[2]
ax3.plot(df_yolo['epoch'], df_yolo['metrics/mAP50(B)'] * 100, color='#10b981', linewidth=2.2, label='Val mAP@50 (%)')
ax3.plot(df_yolo['epoch'], df_yolo['metrics/mAP50-95(B)'] * 100, color='#6366f1', linewidth=2.2, label='Val mAP@50-95 (%)')

max_map50 = df_yolo['metrics/mAP50(B)'].max() * 100
max_map_ep = df_yolo.loc[df_yolo['metrics/mAP50(B)'].idxmax(), 'epoch']
ax3.scatter([max_map_ep], [max_map50], color='#10b981', s=100, zorder=5, edgecolor='#0f172a', linewidth=1.5)
ax3.annotate(
    f'Peak mAP50: {max_map50:.1f}%\n(Epoch {int(max_map_ep)})',
    xy=(max_map_ep, max_map50),
    xytext=(max_map_ep - 22, max_map50 - 14),
    color='#10b981',
    fontsize=9,
    fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='#10b981', lw=1.5)
)

ax3.set_title('Validation Detection Accuracy (mAP)', fontsize=13, fontweight='bold', color='#f8fafc', pad=12)
ax3.set_xlabel('Training Epochs', fontsize=11, color='#cbd5e1')
ax3.set_ylabel('Mean Average Precision (%)', fontsize=11, color='#cbd5e1')
ax3.legend(loc='lower right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)

plt.suptitle('OATrack-VLM: YOLO11n-VHRV Maritime Vessel Detector (60 Epochs)', fontsize=15, fontweight='bold', color='#f8fafc', y=1.02)
plt.tight_layout()

yolo_graph_path1 = loss_graphs_dir / "yolo_detector_loss_graph.png"
yolo_graph_path2 = outputs_dir / "yolo_detector_loss_graph.png"
fig.savefig(yolo_graph_path1, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
fig.savefig(yolo_graph_path2, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close(fig)
print(f"[OK] Saved YOLO detector loss graph -> {yolo_graph_path1}")


# ==============================================================================
# 2. GENERATE GRAPH 2: CONVNEXT-TINY CLASSIFIER LOSS & ACCURACY
# ==============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
fig.patch.set_facecolor('#0f172a')

for ax in axes:
    ax.set_facecolor('#1e293b')
    ax.grid(True, linestyle='--', alpha=0.3, color='#94a3b8')
    ax.tick_params(colors='#e2e8f0', labelsize=10)
    for spine in ax.spines.values():
        spine.set_color('#334155')

# Panel 1: Classifier Loss
ax1 = axes[0]
ax1.plot(df_conv['epoch'], df_conv['train_loss'], color='#38bdf8', linewidth=2.8, marker='o', markersize=7, label='Training Loss')
ax1.plot(df_conv['epoch'], df_conv['val_loss'], color='#f43f5e', linewidth=2.8, marker='s', markersize=7, label='Validation Loss')

for i, row in df_conv.iterrows():
    ax1.annotate(f"{row['train_loss']:.3f}", (row['epoch'], row['train_loss']), textcoords="offset points", xytext=(0, 8), ha='center', color='#38bdf8', fontsize=8.5, fontweight='bold')
    ax1.annotate(f"{row['val_loss']:.3f}", (row['epoch'], row['val_loss']), textcoords="offset points", xytext=(0, 8), ha='center', color='#f43f5e', fontsize=8.5, fontweight='bold')

ax1.set_title('ConvNeXt-Tiny: Cross-Entropy Loss per Epoch', fontsize=13, fontweight='bold', color='#f8fafc', pad=12)
ax1.set_xlabel('Epoch', fontsize=11, color='#cbd5e1')
ax1.set_ylabel('Loss (Cross-Entropy)', fontsize=11, color='#cbd5e1')
ax1.set_xticks(df_conv['epoch'])
ax1.legend(loc='center right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10.5)

# Panel 2: Classifier Accuracy
ax2 = axes[1]
ax2.plot(df_conv['epoch'], df_conv['train_accuracy'] * 100, color='#10b981', linewidth=2.8, marker='o', markersize=7, label='Training Accuracy (%)')
ax2.plot(df_conv['epoch'], df_conv['val_accuracy'] * 100, color='#fbbf24', linewidth=2.8, marker='s', markersize=7, label='Validation Accuracy (%)')

for i, row in df_conv.iterrows():
    ax2.annotate(f"{row['train_accuracy']*100:.1f}%", (row['epoch'], row['train_accuracy']*100), textcoords="offset points", xytext=(0, -14), ha='center', color='#10b981', fontsize=8.5, fontweight='bold')
    ax2.annotate(f"{row['val_accuracy']*100:.1f}%", (row['epoch'], row['val_accuracy']*100), textcoords="offset points", xytext=(0, 8), ha='center', color='#fbbf24', fontsize=8.5, fontweight='bold')

ax2.set_title('ConvNeXt-Tiny: Classification Accuracy (%)', fontsize=13, fontweight='bold', color='#f8fafc', pad=12)
ax2.set_xlabel('Epoch', fontsize=11, color='#cbd5e1')
ax2.set_ylabel('Accuracy (%)', fontsize=11, color='#cbd5e1')
ax2.set_xticks(df_conv['epoch'])
ax2.set_ylim(70, 105)
ax2.legend(loc='lower right', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10.5)

plt.suptitle('OATrack-VLM: Fine-Grained Ship Classifier (TITANIC-FGS-10)', fontsize=15, fontweight='bold', color='#f8fafc', y=1.02)
plt.tight_layout()

conv_graph_path1 = loss_graphs_dir / "convnext_classifier_loss_graph.png"
conv_graph_path2 = outputs_dir / "convnext_classifier_loss_graph.png"
fig.savefig(conv_graph_path1, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
fig.savefig(conv_graph_path2, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close(fig)
print(f"[OK] Saved ConvNeXt classifier loss graph -> {conv_graph_path1}")


# ==============================================================================
# 3. GENERATE UNIFIED COMPREHENSIVE GRAPH (SAVED IN OUTPUTS ROOT & LOSS_GRAPHS)
# ==============================================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 11), dpi=300)
fig.patch.set_facecolor('#0b1329')

for row in axes:
    for ax in row:
        ax.set_facecolor('#162038')
        ax.grid(True, linestyle='--', alpha=0.35, color='#64748b')
        ax.tick_params(colors='#e2e8f0', labelsize=10)
        for spine in ax.spines.values():
            spine.set_color('#334155')

# Top Left: YOLO Total Loss
ax_tl = axes[0, 0]
ax_tl.plot(df_yolo['epoch'], df_yolo['train_total_loss'], color='#38bdf8', linewidth=2.5, label='YOLO Train Total Loss', alpha=0.9)
ax_tl.plot(df_yolo['epoch'], df_yolo['val_total_loss'], color='#f43f5e', linewidth=2.5, label='YOLO Val Total Loss', alpha=0.9)
ax_tl.scatter([min_val_ep], [min_val_loss], color='#fbbf24', s=110, zorder=5, edgecolor='#0b1329', linewidth=1.5)
ax_tl.annotate(
    f'Min Val Loss: {min_val_loss:.3f} (Ep {int(min_val_ep)})',
    xy=(min_val_ep, min_val_loss),
    xytext=(min_val_ep + 5, min_val_loss + 0.35),
    color='#fbbf24',
    fontsize=9.5,
    fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='#fbbf24', lw=1.5)
)
ax_tl.set_title('(A) Vessel Detector (YOLO11n): Total Training vs Validation Loss', fontsize=12.5, fontweight='bold', color='#f8fafc', pad=10)
ax_tl.set_xlabel('Epochs (1 to 60)', fontsize=10.5, color='#cbd5e1')
ax_tl.set_ylabel('Objective Loss', fontsize=10.5, color='#cbd5e1')
ax_tl.legend(loc='upper right', facecolor='#0b1329', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)

# Top Right: YOLO Validation Accuracy (mAP50 & mAP50-95)
ax_tr = axes[0, 1]
ax_tr.plot(df_yolo['epoch'], df_yolo['metrics/mAP50(B)'] * 100, color='#10b981', linewidth=2.5, label='Vessel mAP@50 (Peak: 94.6%)')
ax_tr.plot(df_yolo['epoch'], df_yolo['metrics/mAP50-95(B)'] * 100, color='#a855f7', linewidth=2.5, label='Vessel mAP@50-95 (Peak: 56.4%)')
ax_tr.axhline(94.63, color='#10b981', linestyle=':', alpha=0.6, label='Best Test Benchmark: 94.6%')
ax_tr.set_title('(B) Vessel Detector (YOLO11n): Detection Precision & mAP Trajectory', fontsize=12.5, fontweight='bold', color='#f8fafc', pad=10)
ax_tr.set_xlabel('Epochs (1 to 60)', fontsize=10.5, color='#cbd5e1')
ax_tr.set_ylabel('Detection Accuracy (%)', fontsize=10.5, color='#cbd5e1')
ax_tr.legend(loc='lower right', facecolor='#0b1329', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)

# Bottom Left: ConvNeXt Loss
ax_bl = axes[1, 0]
ax_bl.plot(df_conv['epoch'], df_conv['train_loss'], color='#38bdf8', linewidth=2.5, marker='o', markersize=6.5, label='Classifier Train Loss')
ax_bl.plot(df_conv['epoch'], df_conv['val_loss'], color='#f43f5e', linewidth=2.5, marker='s', markersize=6.5, label='Classifier Val Loss')
for i, row in df_conv.iterrows():
    ax_bl.annotate(f"{row['train_loss']:.3f}", (row['epoch'], row['train_loss']), textcoords="offset points", xytext=(0, 7), ha='center', color='#38bdf8', fontsize=8, fontweight='bold')
    ax_bl.annotate(f"{row['val_loss']:.3f}", (row['epoch'], row['val_loss']), textcoords="offset points", xytext=(0, 7), ha='center', color='#f43f5e', fontsize=8, fontweight='bold')
ax_bl.set_title('(C) Ship Classifier (ConvNeXt-Tiny): Cross-Entropy Training vs Val Loss', fontsize=12.5, fontweight='bold', color='#f8fafc', pad=10)
ax_bl.set_xlabel('Epochs (1 to 5)', fontsize=10.5, color='#cbd5e1')
ax_bl.set_ylabel('Cross-Entropy Loss', fontsize=10.5, color='#cbd5e1')
ax_bl.set_xticks(df_conv['epoch'])
ax_bl.legend(loc='center right', facecolor='#0b1329', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)

# Bottom Right: ConvNeXt Accuracy
ax_br = axes[1, 1]
ax_br.plot(df_conv['epoch'], df_conv['train_accuracy'] * 100, color='#10b981', linewidth=2.5, marker='o', markersize=6.5, label='Classifier Train Acc (%)')
ax_br.plot(df_conv['epoch'], df_conv['val_accuracy'] * 100, color='#fbbf24', linewidth=2.5, marker='s', markersize=6.5, label='Classifier Val Acc (%)')
for i, row in df_conv.iterrows():
    ax_br.annotate(f"{row['train_accuracy']*100:.1f}%", (row['epoch'], row['train_accuracy']*100), textcoords="offset points", xytext=(0, -13), ha='center', color='#10b981', fontsize=8, fontweight='bold')
    ax_br.annotate(f"{row['val_accuracy']*100:.1f}%", (row['epoch'], row['val_accuracy']*100), textcoords="offset points", xytext=(0, 7), ha='center', color='#fbbf24', fontsize=8, fontweight='bold')
ax_br.set_title('(D) Ship Classifier (ConvNeXt-Tiny): Training vs Validation Accuracy', fontsize=12.5, fontweight='bold', color='#f8fafc', pad=10)
ax_br.set_xlabel('Epochs (1 to 5)', fontsize=10.5, color='#cbd5e1')
ax_br.set_ylabel('Top-1 Accuracy (%)', fontsize=10.5, color='#cbd5e1')
ax_br.set_xticks(df_conv['epoch'])
ax_br.set_ylim(70, 105)
ax_br.legend(loc='lower right', facecolor='#0b1329', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)

plt.suptitle('OATrack-VLM: Complete Architecture Training & Validation Loss Dashboard', fontsize=16, fontweight='bold', color='#f8fafc', y=1.01)
plt.tight_layout()

# Save unified graphs to multiple standard destinations
main_paths = [
    outputs_dir / "training_val_loss_graph.png",
    outputs_dir / "model_training_and_validation_loss.png",
    loss_graphs_dir / "model_training_and_validation_loss.png",
    loss_graphs_dir / "training_val_loss_graph.png"
]
for p in main_paths:
    fig.savefig(p, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"[OK] Saved unified dashboard -> {p}")

plt.close(fig)

# Save JSON numerical summary
summary_data = {
    "yolo11n_detector": {
        "dataset": "VHRV Optical Satellite",
        "total_epochs": int(len(df_yolo)),
        "initial_train_loss": round(float(df_yolo.loc[0, 'train_total_loss']), 4),
        "final_train_loss": round(float(df_yolo.loc[len(df_yolo)-1, 'train_total_loss']), 4),
        "initial_val_loss": round(float(df_yolo.loc[0, 'val_total_loss']), 4),
        "min_val_loss": round(float(min_val_loss), 4),
        "min_val_loss_epoch": int(min_val_ep),
        "final_val_loss": round(float(df_yolo.loc[len(df_yolo)-1, 'val_total_loss']), 4),
        "peak_val_map50": round(float(max_map50), 2),
        "peak_val_map50_epoch": int(max_map_ep),
    },
    "convnext_tiny_classifier": {
        "dataset": "TITANIC-FGS-10",
        "total_epochs": int(len(df_conv)),
        "initial_train_loss": round(float(df_conv.loc[0, 'train_loss']), 4),
        "final_train_loss": round(float(df_conv.loc[len(df_conv)-1, 'train_loss']), 4),
        "initial_val_loss": round(float(df_conv.loc[0, 'val_loss']), 4),
        "final_val_loss": round(float(df_conv.loc[len(df_conv)-1, 'val_loss']), 4),
        "initial_train_acc": round(float(df_conv.loc[0, 'train_accuracy']), 4),
        "final_train_acc": round(float(df_conv.loc[len(df_conv)-1, 'train_accuracy']), 4),
        "initial_val_acc": round(float(df_conv.loc[0, 'val_accuracy']), 4),
        "final_val_acc": round(float(df_conv.loc[len(df_conv)-1, 'val_accuracy']), 4),
    }
}

summary_json_path = outputs_dir / "training_loss_summary.json"
with open(summary_json_path, "w") as f:
    json.dump(summary_data, f, indent=2)
with open(loss_graphs_dir / "training_loss_summary.json", "w") as f:
    json.dump(summary_data, f, indent=2)

print(f"[OK] Saved numerical summary -> {summary_json_path}")
print("ALL LOSS GRAPHS GENERATED SUCCESSFULLY.")
