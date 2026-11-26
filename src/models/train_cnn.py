"""Train and evaluate a CNN on one-second OrcaSound Log-Mel spectrograms."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import librosa
import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.models.cnn import CNN_SAMPLE_RATE, OrcaCNN, extract_cnn_spectrogram
from src.models.train import DEFAULT_DATASET_DIR, PROJECT_ROOT, analyze_thresholds, grouped_three_way_split, load_labels


DEFAULT_MODEL_PATH = PROJECT_ROOT / "src" / "models" / "orca_cnn.pt"
DEFAULT_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "cnn_training_metrics.json"
RANDOM_STATE = 42


def build_spectrograms(labels, audio_files):
    images, targets, groups = [], [], []
    total_files = labels["wav_filename"].nunique()
    for index, (filename, rows) in enumerate(labels.groupby("wav_filename", sort=True), start=1):
        if index == 1 or index % 25 == 0 or index == total_files:
            print(f"[{index}/{total_files}] Processing {filename}")
        audio, sample_rate = librosa.load(audio_files[filename], sr=CNN_SAMPLE_RATE, mono=True)
        for row in rows.itertuples(index=False):
            start = int(round(float(row.start_time_s) * sample_rate))
            duration = int(round(float(row.duration_s) * sample_rate))
            chunk = audio[start : start + duration]
            if duration <= 0 or len(chunk) != duration:
                continue
            if len(chunk) < CNN_SAMPLE_RATE:
                chunk = np.pad(chunk, (0, CNN_SAMPLE_RATE - len(chunk)))
            else:
                chunk = chunk[:CNN_SAMPLE_RATE]
            images.append(extract_cnn_spectrogram(chunk, sample_rate))
            targets.append(int(row.label))
            groups.append(filename)
    return np.stack(images).astype(np.float32), np.asarray(targets), np.asarray(groups)


def probabilities(model, loader, device):
    model.eval(); values = []
    with torch.no_grad():
        for inputs, _ in loader:
            values.extend(torch.sigmoid(model(inputs.to(device))).cpu().numpy())
    return np.asarray(values)


def train(dataset_dir, model_path, metrics_path, allow_partial, epochs, batch_size, target_recall):
    torch.manual_seed(RANDOM_STATE); np.random.seed(RANDOM_STATE)
    labels, audio_files, missing_audio = load_labels(dataset_dir, allow_partial)
    images, targets, groups = build_spectrograms(labels, audio_files)
    train_indices, validation_indices, test_indices = grouped_three_way_split(images, targets, groups)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device.type}")
    def loader(indices, shuffle=False):
        dataset = TensorDataset(torch.from_numpy(images[indices]).unsqueeze(1), torch.from_numpy(targets[indices]).float())
        return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)

    train_loader, validation_loader, test_loader = loader(train_indices, True), loader(validation_indices), loader(test_indices)
    model = OrcaCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()
    best_state, best_score = None, -1.0

    for epoch in range(1, epochs + 1):
        model.train(); total_loss = 0.0
        for inputs, labels_batch in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(inputs.to(device)), labels_batch.to(device))
            loss.backward(); optimizer.step(); total_loss += float(loss.item())
        validation_probabilities = probabilities(model, validation_loader, device)
        threshold, analysis = analyze_thresholds(targets[validation_indices], validation_probabilities, target_recall)
        selected = next(item for item in analysis if item["threshold"] == threshold)
        print(f"Epoch {epoch}/{epochs} | loss={total_loss / len(train_loader):.4f} | validation F1={selected['f1']:.3f} | threshold={threshold:.2f}")
        if selected["f1"] > best_score:
            best_score, best_state = selected["f1"], copy.deepcopy(model.state_dict())

    model.load_state_dict(best_state)
    validation_probabilities = probabilities(model, validation_loader, device)
    threshold, analysis = analyze_thresholds(targets[validation_indices], validation_probabilities, target_recall)
    test_probabilities = probabilities(model, test_loader, device)
    predictions = (test_probabilities >= threshold).astype(int)
    matrix = confusion_matrix(targets[test_indices], predictions, labels=[0, 1]).tolist()
    report = classification_report(targets[test_indices], predictions, output_dict=True, zero_division=0)

    model_path.parent.mkdir(parents=True, exist_ok=True); metrics_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.cpu().state_dict(), "threshold": threshold, "sample_rate": CNN_SAMPLE_RATE}, model_path)
    metrics = {"model_path": str(model_path), "model_type": "cnn", "available_windows": int(len(images)), "missing_recordings": len(missing_audio), "train_recordings": int(len(set(groups[train_indices]))), "validation_recordings": int(len(set(groups[validation_indices]))), "test_recordings": int(len(set(groups[test_indices]))), "selected_threshold": threshold, "target_validation_recall": target_recall, "threshold_analysis": analysis, "confusion_matrix": matrix, "classification_report": report}
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"\nCNN saved to: {model_path}\nMetrics saved to: {metrics_path}\nSelected threshold: {threshold:.2f}")
    print("Confusion matrix rows=true [no_orca, orca], columns=predicted [no_orca, orca]:")
    print(np.array(matrix)); print(classification_report(targets[test_indices], predictions, zero_division=0))


def main():
    parser = argparse.ArgumentParser(description="Train the OrcaPath CNN spectrogram classifier.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--target-recall", type=float, default=0.80)
    args = parser.parse_args()
    train(args.dataset_dir, args.model_path, args.metrics_path, args.allow_partial, args.epochs, args.batch_size, args.target_recall)


if __name__ == "__main__":
    main()
