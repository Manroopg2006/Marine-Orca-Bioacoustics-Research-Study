"""CNN model and shared spectrogram preprocessing for OrcaPath."""

from __future__ import annotations

import numpy as np
import librosa
import torch
from torch import nn


CNN_SAMPLE_RATE = 44_100
CNN_MEL_BINS = 128


def extract_cnn_spectrogram(chunk: np.ndarray, sample_rate: int = CNN_SAMPLE_RATE) -> np.ndarray:
    """Return a normalized [mel-bin, time-frame] Log-Mel image for one second of audio."""
    mel = librosa.feature.melspectrogram(
        y=chunk, sr=sample_rate, n_mels=CNN_MEL_BINS, n_fft=2048, hop_length=512, fmax=20_000
    )
    mel_db = librosa.power_to_db(mel, ref=np.max).astype(np.float32)
    return (mel_db - mel_db.mean()) / (mel_db.std() + 1e-6)


class OrcaCNN(nn.Module):
    """Small CNN designed for CPU-friendly one-second spectrogram classification."""

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1), nn.ReLU(), nn.BatchNorm2d(16), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.BatchNorm2d(32), nn.MaxPool2d(2),
            nn.Conv2d(32, 48, kernel_size=3, padding=1), nn.ReLU(), nn.BatchNorm2d(48),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.25), nn.Linear(48, 1))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(inputs)).squeeze(1)
