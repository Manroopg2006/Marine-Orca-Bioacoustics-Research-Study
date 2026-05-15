import os
import sys
import io
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from ..schemas import SpectrogramInfo

router = APIRouter()

PROCESSED_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "processed"
)

SPECTROGRAM_TITLES = {
    "call_clusters.png": "Call Type Clusters (PCA)",
    "call_type_spectrograms.png": "Orca Call Type Spectrograms",
    "clustering.png": "K-Means Cluster Validation",
    "marked_orca_calls.png": "Marked Orca Call Events",
    "orca_test.png": "Orca Detection Test",
    "permutation_test.png": "Permutation Test Results",
    "temporal_analysis.png": "Temporal Pattern Analysis",
}


@router.get("", response_model=List[SpectrogramInfo])
def list_spectrograms():
    results = []
    if not os.path.exists(PROCESSED_DIR):
        return results
    for fname in sorted(os.listdir(PROCESSED_DIR)):
        if fname.endswith(".png"):
            results.append(
                SpectrogramInfo(
                    filename=fname,
                    url=f"/api/spectrograms/{fname}",
                    title=SPECTROGRAM_TITLES.get(fname, fname.replace("_", " ").replace(".png", "").title()),
                )
            )
    return results


@router.get("/{filename}")
def get_spectrogram(filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Spectrogram not found")
    return FileResponse(path, media_type="image/png")


@router.post("/generate")
def generate_spectrogram(
    file_path: str = Query(..., description="Absolute path to WAV file"),
    start_sec: float = Query(0.0),
    end_sec: float = Query(5.0),
):
    """Generate a spectrogram PNG for a specific audio segment."""
    try:
        import librosa
        import librosa.display
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise HTTPException(status_code=500, detail="librosa/matplotlib not installed")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    sr = 44100
    offset = start_sec
    duration = end_sec - start_sec

    audio, sr = librosa.load(file_path, sr=sr, mono=True, offset=offset, duration=duration)
    mel_spec = librosa.feature.melspectrogram(
        y=audio, sr=sr, n_mels=128, n_fft=2048, hop_length=512, fmax=20000
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)

    fig, ax = plt.subplots(figsize=(8, 3), facecolor="#0f172a")
    ax.set_facecolor("#0f172a")
    img = librosa.display.specshow(mel_db, sr=sr, hop_length=512, x_axis="time", y_axis="mel", ax=ax, cmap="magma")
    ax.set_title(f"Mel Spectrogram ({start_sec:.1f}s–{end_sec:.1f}s)", color="white", fontsize=10)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    plt.colorbar(img, ax=ax, format="%+2.0f dB").ax.yaxis.set_tick_params(color="white")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#0f172a")
    plt.close(fig)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
