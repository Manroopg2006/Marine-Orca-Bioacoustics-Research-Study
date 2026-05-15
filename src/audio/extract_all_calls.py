import librosa
import numpy as np
import os
import sys
sys.path.insert(0, '.')
from src.audio.extract_negatives import parse_labels

CHUNK_DURATION = 5
SR = 44100

def extract_chunks_from_file(file_path, sr=SR):
    """Extract 5 second chunks from a file"""
    print(f"Processing {os.path.basename(file_path)}...")
    audio, sr = librosa.load(file_path, sr=sr, mono=True)
    chunk_samples = CHUNK_DURATION * sr
    chunks = []

    for start in range(0, len(audio) - chunk_samples, chunk_samples):
        chunk = audio[start:start + chunk_samples]
        mel_spec = librosa.feature.melspectrogram(
            y=chunk, sr=sr, n_mels=64,
            n_fft=512, hop_length=128, fmax=20000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        chunks.append({
            'features': mel_spec_db.flatten(),
            'start_sec': start / sr,
            'file': os.path.basename(file_path)
        })
    return chunks

def extract_labeled_calls(audio_file, label_file, sr=SR):
    """Extract individual calls using label file"""
    print(f"Processing labeled {os.path.basename(audio_file)}...")
    audio, sr = librosa.load(audio_file, sr=sr, mono=True)
    calls = parse_labels(label_file)
    fixed_samples = int(1.5 * sr)
    chunks = []

    for start_sec, end_sec in calls:
        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        call = audio[start_sample:end_sample]

        if len(call) < fixed_samples:
            call = np.pad(call, (0, fixed_samples - len(call)))
        else:
            call = call[:fixed_samples]

        mel_spec = librosa.feature.melspectrogram(
            y=call, sr=sr, n_mels=64,
            n_fft=512, hop_length=128, fmax=20000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        chunks.append({
            'features': mel_spec_db.flatten(),
            'start_sec': start_sec,
            'file': os.path.basename(audio_file)
        })
    return chunks

all_chunks = []

# 1 — Labeled calls from July 2019 test file
audio_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_.wav"
label_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_labels-SV_200210_only_calls.txt"
all_chunks.extend(extract_labeled_calls(audio_file, label_file))

# 2 — All Sept 27 2017 files (no labels, use chunks)
sept_2017_dir = "data/raw_audio/labeled/orca"
for f in sorted(os.listdir(sept_2017_dir)):
    if f.startswith("OS_9_27_2017") and f.endswith(".wav"):
        file_path = os.path.join(sept_2017_dir, f)
        all_chunks.extend(extract_chunks_from_file(file_path))

# 3 — July 2019 full recordings
july_2019_files = [
    "data/raw_audio/labeled/orca/OS_7_05_2019_07_54_00_.wav",
    "data/raw_audio/labeled/orca/OS_7_05_2019_08_54_00_.wav",
    "data/raw_audio/labeled/orca/OS_7_05_2019_09_24_00_.wav"
]
for f in july_2019_files:
    all_chunks.extend(extract_chunks_from_file(f))

# Save
X = np.array([c['features'] for c in all_chunks])
files = np.array([c['file'] for c in all_chunks])
starts = np.array([c['start_sec'] for c in all_chunks])

os.makedirs("data/processed", exist_ok=True)
np.save("data/processed/all_call_features.npy", X)
np.save("data/processed/all_call_files.npy", files)
np.save("data/processed/all_call_starts.npy", starts)

print(f"\nTotal chunks extracted: {len(X)}")
print(f"Feature vector size: {X.shape[1]}")
print(f"Files included: {np.unique(files)}")