"""Shared feature extraction and inference for the OrcaPath classifier."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import librosa
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.environ.get("ORCA_MODEL_PATH", PROJECT_ROOT / "src" / "models" / "orca_detector.pkl"))
CNN_MODEL_PATH = Path(os.environ.get("ORCA_CNN_MODEL_PATH", PROJECT_ROOT / "src" / "models" / "orca_cnn.pt"))
CHUNK_DURATION_SECONDS = 1
SAMPLE_RATE = 44_100


@lru_cache(maxsize=1)
def get_model() -> Any:
    """Load the trained model once per running API process."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file was not found at {MODEL_PATH}. Train a model or set ORCA_MODEL_PATH before starting the API."
        )
    return joblib.load(MODEL_PATH)


def get_model_and_threshold() -> tuple[Any, float]:
    """Support both legacy model files and new training bundles."""
    loaded = get_model()
    if isinstance(loaded, dict) and "model" in loaded:
        model = loaded["model"]
        saved_threshold = float(loaded.get("threshold", 0.5))
    else:
        model = loaded
        saved_threshold = 0.5
    return model, float(os.environ.get("ORCA_THRESHOLD", saved_threshold))


@lru_cache(maxsize=1)
def get_cnn_model_and_threshold() -> tuple[Any, float]:
    """Load the optional CNN model only when CNN inference is enabled."""
    if not CNN_MODEL_PATH.exists():
        raise FileNotFoundError(f"CNN model was not found at {CNN_MODEL_PATH}. Train it or set ORCA_CNN_MODEL_PATH.")
    import torch
    from src.models.cnn import OrcaCNN

    checkpoint = torch.load(CNN_MODEL_PATH, map_location="cpu")
    model = OrcaCNN()
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, float(os.environ.get("ORCA_THRESHOLD", checkpoint.get("threshold", 0.5)))


def extract_features(chunk: np.ndarray, sample_rate: int) -> np.ndarray:
    """Create the fixed-size log-Mel summary used by training and inference.

    Means and standard deviations across time retain frequency information while
    keeping the Random Forest input small enough to retrain locally.
    """
    mel_spec = librosa.feature.melspectrogram(
        y=chunk,
        sr=sample_rate,
        n_mels=128,
        n_fft=2048,
        hop_length=512,
        fmax=20_000,
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)
    return np.concatenate([mel_db.mean(axis=1), mel_db.std(axis=1)]).astype(np.float32)


def analyze_audio(
    file_path: str | Path,
    chunk_duration: int = CHUNK_DURATION_SECONDS,
    sample_rate: int = SAMPLE_RATE,
    threshold_override: float | None = None,
) -> dict[str, Any]:
    """Classify an audio file and return a small, UI-ready result payload."""
    path = Path(file_path)
    audio, sr = librosa.load(path, sr=sample_rate, mono=True)
    duration_seconds = round(len(audio) / sr, 2)
    chunk_samples = chunk_duration * sr
    if len(audio) == 0:
        raise ValueError("The audio file contains no samples.")

    chunks = [audio[start : start + chunk_samples] for start in range(0, len(audio), chunk_samples)]
    backend = os.environ.get("ORCA_MODEL_BACKEND", "random_forest").lower()
    if backend == "cnn":
        model, threshold = get_cnn_model_and_threshold()
        import torch
        from src.models.cnn import extract_cnn_spectrogram
    elif backend == "random_forest":
        model, threshold = get_model_and_threshold()
    else:
        raise ValueError("ORCA_MODEL_BACKEND must be 'random_forest' or 'cnn'.")
    if threshold_override is not None:
        threshold = threshold_override
    detections: list[dict[str, float]] = []
    confidences: list[float] = []

    segment_scores: list[dict[str, float | bool]] = []

    for index, chunk in enumerate(chunks):
        if len(chunk) < chunk_samples:
            chunk = np.pad(chunk, (0, chunk_samples - len(chunk)))
        if backend == "cnn":
            spectrogram = extract_cnn_spectrogram(chunk, sr)
            with torch.no_grad():
                probability = float(torch.sigmoid(model(torch.from_numpy(spectrogram).unsqueeze(0).unsqueeze(0))).item())
        else:
            probability = float(model.predict_proba(extract_features(chunk, sr).reshape(1, -1))[0][1])
        confidences.append(probability)

        is_detected = probability >= threshold

        segment_scores.append({
        "start_sec": round(index * chunk_duration, 2),
        "end_sec": round(min((index + 1) * chunk_duration, duration_seconds), 2),
        "confidence": round(probability, 3),
        "detected": is_detected,
     })

        if is_detected:
            detections.append({
                "start_sec": round(index * chunk_duration, 2),
                "end_sec": round(min((index + 1) * chunk_duration, duration_seconds), 2),
                "confidence": round(probability, 3),
            })

    return {
        "classification": "orca" if detections else "no_orca",
        "confidence": round(max(confidences, default=0.0), 3),
        "duration_seconds": duration_seconds,
        "sample_rate": sr,
        "segments_analyzed": len(chunks),
        "total_detections": len(detections),
        "detections": detections,
        "segment_scores": segment_scores,
    }


def detect_orca(file_path: str | Path, **kwargs: Any) -> list[dict[str, float]]:
    """Backwards-compatible helper that returns only detected segments."""
    return analyze_audio(file_path, **kwargs)["detections"]
