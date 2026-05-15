import os
import sys
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List
from ..schemas import DetectResponse

router = APIRouter()

# Add project root to path so we can import src modules
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@router.get("/files")
def list_audio_files():
    """List available labeled audio files in the project."""
    audio_root = os.path.join(PROJECT_ROOT, "data", "raw_audio")
    files = []
    if not os.path.exists(audio_root):
        return {"files": files}
    for root, _, fnames in os.walk(audio_root):
        for fname in fnames:
            if fname.endswith(".wav"):
                rel_path = os.path.relpath(os.path.join(root, fname), PROJECT_ROOT)
                files.append({"filename": fname, "path": rel_path.replace("\\", "/")})
    return {"files": files}


@router.post("/detect", response_model=DetectResponse)
async def detect_from_upload(
    file: UploadFile = File(...),
    location: str = Form("Unknown"),
    lat: float = Form(48.0),
    lon: float = Form(-122.9),
    date: str = Form(""),
):
    """Upload a WAV file and run orca detection."""
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")

    try:
        from src.models.detect import detect_orca
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Could not load ML model: {e}")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        detections = detect_orca(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {e}")
    finally:
        os.unlink(tmp_path)

    return DetectResponse(
        file=file.filename,
        location=location,
        total_detections=len(detections),
        detections=detections,
    )
