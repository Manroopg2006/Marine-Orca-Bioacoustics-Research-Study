import os
import librosa
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import sys
sys.path.insert(0, '.')
from src.audio.spectrogram import load_audio
from src.audio.extract_negatives import extract_no_orca_chunks
import joblib


# Clear old cache
if os.path.exists("data/processed/chunks_X.npy"):
    os.remove("data/processed/chunks_X.npy")
    os.remove("data/processed/chunks_y.npy")
    print("Cleared old cache")

CHUNK_DURATION = 5
CHUNKS_FILE = "data/processed/chunks_X.npy"
LABELS_FILE = "data/processed/chunks_y.npy"

def chunk_audio(file_path, label):
    audio, sr = load_audio(file_path)
    chunk_samples = CHUNK_DURATION * sr
    chunks = []
    for start in range(0, len(audio) - chunk_samples, chunk_samples):
        chunk = audio[start:start + chunk_samples]
        mel_spec = librosa.feature.melspectrogram(
            y=chunk, sr=sr, n_mels=128,
            n_fft=2048, hop_length=512, fmax=20000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        chunks.append((mel_spec_db.flatten(), label))
    return chunks

X, y = [], []

# Add confirmed no-orca chunks from labeled file
audio_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_.wav"
label_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_labels-SV_200210_only_calls.txt"
print("Extracting confirmed no-orca chunks...")
no_orca_features = extract_no_orca_chunks(audio_file, label_file)
for features in no_orca_features:
    X.append(features)
    y.append(0)
print(f"Got {len(no_orca_features)} no-orca chunks")

# Add orca chunks
orca_files = [f"data/raw_audio/labeled/orca/{f}" for f in os.listdir("data/raw_audio/labeled/orca") if f.endswith(".wav")]
for idx, file_path in enumerate(orca_files):
    print(f"Processing orca file {idx+1}/{len(orca_files)}: {file_path}")
    chunks = chunk_audio(file_path, 1)
    for features, label in chunks:
        X.append(features)
        y.append(label)

X = np.array(X)
y = np.array(y)
np.save(CHUNKS_FILE, X)
np.save(LABELS_FILE, y)

print(f"\nTotal chunks: {len(X)}")
print(f"Orca chunks: {int(sum(y))}")
print(f"No orca chunks: {int(len(y) - sum(y))}")

from sklearn.utils import resample

# Separate classes
X_orca = X[y == 1]
y_orca = y[y == 1]
X_no_orca = X[y == 0]
y_no_orca = y[y == 0]

print(f"Before balancing - Orca: {len(X_orca)}, No orca: {len(X_no_orca)}")

# Upsample no-orca to match orca count
X_no_orca_upsampled, y_no_orca_upsampled = resample(
    X_no_orca, y_no_orca,
    replace=True,
    n_samples=len(X_orca),
    random_state=42
)

# Combine back
X = np.vstack([X_orca, X_no_orca_upsampled])
y = np.hstack([y_orca, y_no_orca_upsampled])

print(f"After balancing - Orca: {len(X_orca)}, No orca: {len(X_no_orca_upsampled)}")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

os.makedirs("src/models", exist_ok=True)
joblib.dump(model, "src/models/orca_detector.pkl")
print("Model saved to src/models/orca_detector.pkl")