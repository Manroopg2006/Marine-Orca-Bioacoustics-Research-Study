"""Train the OrcaPath classifier from the extracted OrcaSound competition data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.model_selection import GroupShuffleSplit

from src.models.detect import SAMPLE_RATE, extract_features


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_DIR = PROJECT_ROOT / "data" / "raw_audio" / "orcasound"
DEFAULT_MODEL_PATH = PROJECT_ROOT / "src" / "models" / "orca_detector.pkl"
DEFAULT_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "training_metrics.json"
RANDOM_STATE = 42


def load_labels(dataset_dir: Path, allow_partial: bool) -> tuple[pd.DataFrame, dict[str, Path], list[str]]:
    """Load valid training labels and validate every referenced audio file."""
    labels_path = dataset_dir / "train.csv"
    audio_dir = dataset_dir / "train_audio_files"
    if not labels_path.exists() or not audio_dir.exists():
        raise FileNotFoundError(f"Expected {labels_path} and {audio_dir}.")

    labels = pd.read_csv(labels_path)
    required_columns = {"wav_filename", "start_time_s", "duration_s", "Expected"}
    missing_columns = required_columns - set(labels.columns)
    if missing_columns:
        raise ValueError(f"train.csv is missing columns: {', '.join(sorted(missing_columns))}")

    audio_files = {path.name: path for path in audio_dir.rglob("*.wav")}
    referenced_files = set(labels["wav_filename"].astype(str))
    missing_audio = sorted(referenced_files - set(audio_files))
    available_labels = labels[labels["wav_filename"].isin(audio_files)].copy()

    print(f"Labels: {len(labels):,} windows across {len(referenced_files):,} recordings")
    print(f"Audio: {len(audio_files):,} WAV files available")
    print(f"Usable: {len(available_labels):,} windows across {available_labels['wav_filename'].nunique():,} recordings")
    print(f"Missing: {len(missing_audio):,} labeled recordings")

    if missing_audio and not allow_partial:
        raise RuntimeError(
            "The dataset is incomplete. Re-extract the remaining WAV files, or rerun with --allow-partial "
            "to deliberately train on only the available recordings."
        )
    if available_labels.empty:
        raise RuntimeError("No labeled WAV files are available for training.")

    available_labels["label"] = (available_labels["Expected"].astype(float) >= 0.5).astype(int)
    return available_labels, audio_files, missing_audio


def build_feature_matrix(labels: pd.DataFrame, audio_files: dict[str, Path]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load each recording once and turn each labeled one-second window into features."""
    features: list[np.ndarray] = []
    targets: list[int] = []
    groups: list[str] = []

    for index, (filename, rows) in enumerate(labels.groupby("wav_filename", sort=True), start=1):
        print(f"[{index}/{labels['wav_filename'].nunique()}] Processing {filename}")
        audio, sample_rate = librosa.load(audio_files[filename], sr=SAMPLE_RATE, mono=True)
        for row in rows.itertuples(index=False):
            start_sample = int(round(float(row.start_time_s) * sample_rate))
            duration_samples = int(round(float(row.duration_s) * sample_rate))
            if duration_samples <= 0:
                continue
            chunk = audio[start_sample : start_sample + duration_samples]
            if len(chunk) != duration_samples:
                continue
            # The provided labels are one second. Padding keeps a consistent feature shape if needed.
            if duration_samples < SAMPLE_RATE:
                chunk = np.pad(chunk, (0, SAMPLE_RATE - duration_samples))
            elif duration_samples > SAMPLE_RATE:
                chunk = chunk[:SAMPLE_RATE]
            features.append(extract_features(chunk, sample_rate))
            targets.append(int(row.label))
            groups.append(filename)

    if not features:
        raise RuntimeError("No valid labeled audio windows could be extracted.")
    return np.vstack(features), np.asarray(targets), np.asarray(groups)


def grouped_three_way_split(
    features: np.ndarray, targets: np.ndarray, groups: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create recording-level train, validation, and final-test partitions."""
    for seed_offset in range(20):
        test_splitter = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=RANDOM_STATE + seed_offset)
        train_validation_indices, test_indices = next(test_splitter.split(features, targets, groups))
        validation_splitter = GroupShuffleSplit(n_splits=1, test_size=0.1765, random_state=RANDOM_STATE + seed_offset)
        train_relative, validation_relative = next(
            validation_splitter.split(
                features[train_validation_indices],
                targets[train_validation_indices],
                groups[train_validation_indices],
            )
        )
        train_indices = train_validation_indices[train_relative]
        validation_indices = train_validation_indices[validation_relative]
        splits = (train_indices, validation_indices, test_indices)
        if all(len(np.unique(targets[indices])) == 2 for indices in splits):
            return splits
    raise RuntimeError("Could not create recording-level train, validation, and test splits containing both classes.")


def analyze_thresholds(
    labels: np.ndarray, probabilities: np.ndarray, target_recall: float
) -> tuple[float, list[dict[str, float]]]:
    """Choose the most precise threshold meeting the recall target on validation data."""
    results: list[dict[str, float]] = []
    for threshold in np.arange(0.05, 1.0, 0.05):
        predictions = (probabilities >= threshold).astype(int)
        results.append({
            "threshold": round(float(threshold), 2),
            "precision": round(float(precision_score(labels, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(labels, predictions, zero_division=0)), 4),
            "f1": round(float(f1_score(labels, predictions, zero_division=0)), 4),
        })
    eligible = [result for result in results if result["recall"] >= target_recall]
    if eligible:
        selected = max(eligible, key=lambda result: (result["precision"], result["f1"], result["threshold"]))
    else:
        selected = max(results, key=lambda result: (result["recall"], result["precision"]))
        print(f"Warning: no threshold achieved the {target_recall:.0%} recall target on validation data.")
    return float(selected["threshold"]), results


def train(
    dataset_dir: Path, model_path: Path, metrics_path: Path, allow_partial: bool, target_recall: float
) -> None:
    labels, audio_files, missing_audio = load_labels(dataset_dir, allow_partial)
    features, targets, groups = build_feature_matrix(labels, audio_files)
    train_indices, validation_indices, test_indices = grouped_three_way_split(features, targets, groups)

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced_subsample",
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    model.fit(features[train_indices], targets[train_indices])
    validation_probabilities = model.predict_proba(features[validation_indices])[:, 1]
    threshold, threshold_results = analyze_thresholds(targets[validation_indices], validation_probabilities, target_recall)
    predictions = (model.predict_proba(features[test_indices])[:, 1] >= threshold).astype(int)
    report = classification_report(targets[test_indices], predictions, output_dict=True, zero_division=0)
    matrix = confusion_matrix(targets[test_indices], predictions, labels=[0, 1]).tolist()

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump({"model": model, "threshold": threshold, "chunk_duration_seconds": 1}, model_path)
    metrics = {
        "model_path": str(model_path),
        "feature_count": int(features.shape[1]),
        "available_windows": int(len(features)),
        "missing_recordings": len(missing_audio),
        "train_recordings": int(len(set(groups[train_indices]))),
        "validation_recordings": int(len(set(groups[validation_indices]))),
        "test_recordings": int(len(set(groups[test_indices]))),
        "selected_threshold": threshold,
        "target_validation_recall": target_recall,
        "threshold_analysis": threshold_results,
        "confusion_matrix": matrix,
        "classification_report": report,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"\nModel saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    print(f"Selected threshold: {threshold:.2f} (validation recall target: {target_recall:.0%})")
    print("Confusion matrix rows=true [no_orca, orca], columns=predicted [no_orca, orca]:")
    print(np.array(matrix))
    print(classification_report(targets[test_indices], predictions, zero_division=0))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the OrcaPath one-second audio classifier.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metrics-path", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--allow-partial", action="store_true", help="Train only on labeled recordings present locally.")
    parser.add_argument("--target-recall", type=float, default=0.80, help="Validation recall target used to choose the detection threshold.")
    args = parser.parse_args()
    if not 0 < args.target_recall <= 1:
        parser.error("--target-recall must be greater than 0 and at most 1.")
    train(args.dataset_dir, args.model_path, args.metrics_path, args.allow_partial, args.target_recall)


if __name__ == "__main__":
    main()
