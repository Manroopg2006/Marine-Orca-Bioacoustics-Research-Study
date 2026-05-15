import librosa
import numpy as np
import os

def parse_labels(label_file):
    """Read label file and return list of (start, end) orca call timestamps"""
    calls = []
    with open(label_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[2] == 'call':
                try:
                    start = float(parts[0])
                    end = float(parts[1])
                    calls.append((start, end))
                except:
                    continue
    return calls

def extract_call_features(audio_file, label_file, sr=44100, fixed_length=1.5):
    """Extract mel spectrogram features for each labeled orca call"""
    print(f"Loading {os.path.basename(audio_file)}...")
    audio, sr = librosa.load(audio_file, sr=sr, mono=True)
    calls = parse_labels(label_file)
    print(f"Found {len(calls)} labeled calls")

    features = []
    timestamps = []
    fixed_samples = int(fixed_length * sr)

    for start_sec, end_sec in calls:
        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        call = audio[start_sample:end_sample]

        # Pad or trim to fixed length
        if len(call) < fixed_samples:
            call = np.pad(call, (0, fixed_samples - len(call)))
        else:
            call = call[:fixed_samples]

        # Extract mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=call, sr=sr, n_mels=64,
            n_fft=512, hop_length=128, fmax=20000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        features.append(mel_spec_db.flatten())
        timestamps.append((start_sec, end_sec))

    return np.array(features), timestamps

# Extract calls
audio_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_.wav"
label_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_labels-SV_200210_only_calls.txt"

X_calls, timestamps = extract_call_features(audio_file, label_file)
print(f"\nExtracted {len(X_calls)} individual call features")
print(f"Feature vector size: {X_calls.shape[1]}")

# Save
os.makedirs("data/processed", exist_ok=True)
np.save("data/processed/call_features.npy", X_calls)
np.save("data/processed/call_timestamps.npy", np.array(timestamps))
print("Saved to data/processed/")