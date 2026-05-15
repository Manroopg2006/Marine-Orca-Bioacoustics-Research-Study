import sounddevice as sd
import librosa
import librosa.display
import time
import threading
import msvcrt
import matplotlib.pyplot as plt
import numpy as np

audio, sr = librosa.load("data/raw_audio/labeled/orca/OS_7_05_2019_07_54_00_.wav", sr=44100, mono=True)

start_sample = 0
end_sample = 25 * sr  # just 25 seconds
audio_clip = audio[start_sample:end_sample]

marks = []
mark_seconds = []
start_time = None

def print_timer(duration):
    while True:
        elapsed = time.time() - start_time
        mins = int(elapsed // 60)
        secs = elapsed % 60
        print(f"\r⏱ {mins}:{secs:05.2f}  | marks: {marks}", end="", flush=True)
        if elapsed >= duration:
            break
        time.sleep(0.1)

def listen_for_marks(duration):
    while True:
        elapsed = time.time() - start_time
        if elapsed >= duration:
            break
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':
                mins = int(elapsed // 60)
                secs = elapsed % 60
                marks.append(f"{mins}:{secs:05.2f}")
                mark_seconds.append(elapsed)
        time.sleep(0.05)

duration = len(audio_clip) / sr
start_time = time.time()

timer_thread = threading.Thread(target=print_timer, args=(duration,))
key_thread = threading.Thread(target=listen_for_marks, args=(duration,))

timer_thread.start()
key_thread.start()

sd.play(audio_clip, sr)
sd.wait()

timer_thread.join()
key_thread.join()

print(f"\n\nYour marked timestamps:")
for m in marks:
    print(f"  🐋 {m}")

# --- Show spectrogram with your marks ---
mel_spec = librosa.feature.melspectrogram(y=audio_clip, sr=sr, n_mels=128, n_fft=2048, hop_length=512, fmax=20000)
mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

plt.figure(figsize=(14, 5))
librosa.display.specshow(mel_spec_db, sr=sr, x_axis='time', y_axis='mel', fmax=20000)
plt.colorbar(format='%+2.0f dB')
plt.title("First 25 Seconds - Your Marked Orca Calls")

# Draw a red vertical line at each mark
for t in mark_seconds:
    plt.axvline(x=t, color='red', linewidth=1.5, linestyle='--', label='orca mark')

plt.tight_layout()
plt.savefig("data/processed/marked_orca_calls.png")
plt.show()