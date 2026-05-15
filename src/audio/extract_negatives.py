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

def extract_no_orca_chunks(audio_file, label_file, chunk_duration=5, sr=44100):
    """Extract chunks from audio that don't overlap with any orca call"""
    audio, sr = librosa.load(audio_file, sr=sr, mono=True)
    calls = parse_labels(label_file)
    chunk_samples = chunk_duration * sr
    no_orca_chunks = []

    for start in range(0, len(audio) - chunk_samples, chunk_samples):
        end = start + chunk_samples
        start_sec = start / sr
        end_sec = end / sr

        # Check if this chunk overlaps with any orca call
        overlaps = any(s < end_sec and e > start_sec for s, e in calls)

        if not overlaps:
            chunk = audio[start:end]
            mel_spec = librosa.feature.melspectrogram(
                y=chunk, sr=sr, n_mels=128,
                n_fft=2048, hop_length=512, fmax=20000
            )
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            no_orca_chunks.append(mel_spec_db.flatten())

    return no_orca_chunks

# Test it
audio_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_.wav"
label_file = "data/raw_audio/labeled/orca/test-only/OS_7_05_2019_08_24_00_labels-SV_200210_only_calls.txt"

chunks = extract_no_orca_chunks(audio_file, label_file)
print(f"Extracted {len(chunks)} confirmed no-orca chunks from same recording")