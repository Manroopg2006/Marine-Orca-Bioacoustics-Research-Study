import librosa
import numpy as np
import joblib
import os
import pandas as pd

model = joblib.load("src/models/orca_detector.pkl")

def detect_orca(file_path, chunk_duration=5, sr=44100):
    print(f"Loading {os.path.basename(file_path)}...")
    audio, sr = librosa.load(file_path, sr=sr, mono=True)
    chunk_samples = chunk_duration * sr
    total_chunks = len(range(0, len(audio) - chunk_samples, chunk_samples))
    print(f"Duration: {len(audio)/sr/3600:.1f} hours | {total_chunks} chunks")
    detections = []

    for i, start in enumerate(range(0, len(audio) - chunk_samples, chunk_samples)):
        if i % 100 == 0:
            print(f"  Processing chunk {i}/{total_chunks}...")
        chunk = audio[start:start + chunk_samples]
        mel_spec = librosa.feature.melspectrogram(
            y=chunk, sr=sr, n_mels=128,
            n_fft=2048, hop_length=512, fmax=20000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        features = mel_spec_db.flatten().reshape(1, -1)
        prediction = model.predict(features)[0]
        confidence = model.predict_proba(features)[0][1]

        if prediction == 1:
            detections.append({
                "start_sec": start / sr,
                "end_sec": (start + chunk_samples) / sr,
                "confidence": round(confidence, 3)
            })

    return detections

# File 1 — Oct 25 1997
file1 = r"C:\Users\xxman\data\raw_audio\onc_digby\KWSR_1997-10-25_CenterForWhaleResearch_DyesInlet.wav"
detections1 = detect_orca(file1)
df1 = pd.DataFrame(detections1)
df1['file'] = os.path.basename(file1)
df1['location'] = 'Dyes Inlet South'
df1['lat'] = 47.6181
df1['lon'] = -122.6865
df1['date'] = '1997-10-25'
print(f"File 1: {len(df1)} detections")

# File 2 — Oct 25-27 1997 (3 day recording)
file2 = r"C:\Users\xxman\data\raw_audio\onc_digby\KWSR_1997-10-25to27_CWR_DyesInlet.wav"
detections2 = detect_orca(file2)
df2 = pd.DataFrame(detections2)
df2['file'] = os.path.basename(file2)
df2['location'] = 'Dyes Inlet North'
df2['lat'] = 47.6534  # slightly north — different position
df2['lon'] = -122.6950
df2['date'] = '1997-10-26'
print(f"File 2: {len(df2)} detections")

# File 3 — Orcasound Lab, San Juan Island Sept 27 2017
file3 = r"C:\projects\orcapath-ai\data\raw_audio\labeled\orca\OS_9_27_2017_08_03_00_.wav"
detections3 = detect_orca(file3)
df3 = pd.DataFrame(detections3)
df3['file'] = os.path.basename(file3)
df3['location'] = 'Orcasound Lab - San Juan Island'
df3['lat'] = 48.5583
df3['lon'] = -123.1650
df3['date'] = '2017-09-27'
print(f"File 3: {len(df3)} detections")

# Update combined save
df_all = pd.concat([df1, df2, df3], ignore_index=True)
df_all.to_csv("data/processed/detections.csv", index=False)
print(f"\nTotal detections: {len(df_all)}")