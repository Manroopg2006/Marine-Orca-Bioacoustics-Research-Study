import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os

def load_audio(file_path, sample_rate=44100):
    """Load a WAV file"""
    audio, sr = librosa.load(file_path, sr=sample_rate, mono=True)
    print(f"Loaded: {os.path.basename(file_path)} | Duration: {len(audio)/sr:.1f}s | Sample rate: {sr}Hz")
    return audio, sr

def generate_spectrogram(audio, sr, title="Spectrogram", save_path=None, show=True):
    """Convert audio to mel spectrogram"""
    # Orca calls are high frequency — use higher n_fft for better resolution
    mel_spec = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=128,
        n_fft=2048,
        hop_length=512,
        fmax=20000  # Focus up to 20kHz — orca range
    )
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

    plt.figure(figsize=(12, 4))
    librosa.display.specshow(mel_spec_db, sr=sr, x_axis='time', y_axis='mel', fmax=20000)
    plt.colorbar(format='%+2.0f dB')
    plt.title(title)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        print(f"Saved to: {save_path}")
    if show:
        plt.show()
    plt.close()

    return mel_spec_db


# Test it
if __name__ == "__main__":
    # Test on one orca file
    orca_file = "data/raw_audio/labeled/orca/OS_7_05_2019_07_54_00_.wav"
    audio, sr = load_audio(orca_file)
    generate_spectrogram(audio, sr, title="Orca Recording", save_path="data/processed/orca_test.png")