import librosa
import numpy as np
import os
import sys
sys.path.insert(0, '.')
from src.audio.extract_negatives import parse_labels

SR = 44100
FIXED_LENGTH = 1.5

def extract_watkins_calls(folder_path, sr=SR):
    """Extract features from Watkins killer whale clips"""
    fixed_samples = int(FIXED_LENGTH * sr)
    features = []
    files = []

    for f in sorted(os.listdir(folder_path)):
        if f.endswith(".wav") or f.endswith(".WAV"):
            file_path = os.path.join(folder_path, f)
            try:
                audio, sr = librosa.load(file_path, sr=sr, mono=True)
                
                # Pad or trim to fixed length
                if len(audio) < fixed_samples:
                    audio = np.pad(audio, (0, fixed_samples - len(audio)))
                else:
                    audio = audio[:fixed_samples]

                mel_spec = librosa.feature.melspectrogram(
                    y=audio, sr=sr, n_mels=64,
                    n_fft=512, hop_length=128, fmax=20000
                )
                mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
                features.append(mel_spec_db.flatten())
                files.append(f)
                print(f"  Extracted: {f}")
            except Exception as e:
                print(f"  Skipped {f}: {e}")

    return np.array(features), files

# Extract Watkins calls
print("Extracting Watkins killer whale calls...")
watkins_dir = "data/raw_audio/watkins/killer_whale/sound"
X_watkins, watkins_files = extract_watkins_calls(watkins_dir)
print(f"Extracted {len(X_watkins)} Watkins calls")

# Load existing labeled calls
X_existing = np.load("data/processed/call_features.npy")
print(f"Existing labeled calls: {len(X_existing)}")

# Combine
X_combined = np.vstack([X_existing, X_watkins])
source_labels = np.array(
    ['orcasound'] * len(X_existing) + 
    ['watkins'] * len(X_watkins)
)

print(f"\nTotal combined: {len(X_combined)}")
np.save("data/processed/combined_call_features.npy", X_combined)
np.save("data/processed/combined_call_sources.npy", source_labels)
print("Saved combined features")