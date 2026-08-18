import os
import tempfile
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import soundfile as sf
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from ..schemas import DetectResponse
from ..database import get_db
from ..model_metadata import get_model_metadata
from ..models import Analysis, AnalysisDetection, AnalysisSegment
router = APIRouter()

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_DURATION_SECONDS = 10 * 60
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_UPLOADS = 5
recent_uploads: dict[str, deque[float]] = defaultdict(deque)
rate_limit_lock = threading.Lock()


def enforce_upload_rate_limit(client_ip: str) -> None:
    """Simple in-memory limit for the public demo; use WAF/Redis when scaling."""
    now = time.monotonic()
    with rate_limit_lock:
        uploads = recent_uploads[client_ip]
        while uploads and now - uploads[0] > RATE_LIMIT_WINDOW_SECONDS:
            uploads.popleft()
        if len(uploads) >= RATE_LIMIT_MAX_UPLOADS:
            raise HTTPException(
                status_code=429,
                detail="Upload limit reached. Please wait a minute before trying again.",
            )
        uploads.append(now)


@router.get("/files")
def list_audio_files():
    """List available labeled audio files in the project."""
    audio_root = PROJECT_ROOT / "data" / "raw_audio"
    files = []
    if not audio_root.exists():
        return {"files": files}
    for root, _, fnames in os.walk(audio_root):
        for fname in fnames:
            if fname.endswith(".wav"):
                rel_path = os.path.relpath(os.path.join(root, fname), PROJECT_ROOT)
                files.append({"filename": fname, "path": rel_path.replace("\\", "/")})
    return {"files": files}


@router.post("/detect", response_model=DetectResponse)
async def detect_from_upload(
    request: Request,
    file: UploadFile = File(...),
    threshold: float = Form(0.4),
    db: Session = Depends(get_db),
):
    """Upload a WAV file and return a simple Orca / No Orca classification."""
    if not file.filename or not file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")
    if not 0.05 <= threshold <= 0.95:
        raise HTTPException(status_code=400, detail="Threshold must be between 0.05 and 0.95")
    enforce_upload_rate_limit(request.client.host if request.client else "unknown")

    try:
        from src.models.detect import analyze_audio
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Could not load ML model: {e}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Files must be smaller than 50 MB")
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        try:
            audio_info = sf.info(tmp_path)
        except RuntimeError as error:
            raise ValueError("The uploaded file is not a readable WAV recording.") from error
        if audio_info.format != "WAV":
            raise ValueError("The uploaded file is not a WAV recording.")
        duration_seconds = audio_info.frames / audio_info.samplerate
        if duration_seconds > MAX_DURATION_SECONDS:
            raise HTTPException(
                status_code=413,
                detail="Recordings must be 10 minutes or shorter.",
            )
        result = analyze_audio(tmp_path, threshold_override=threshold)
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not analyze this WAV file: {e}")
    finally:
        os.unlink(tmp_path)

    metadata = get_model_metadata()
    analysis = Analysis(
        file_name=file.filename,
        threshold=threshold,
        model_version=metadata["model_version"],
        **{key: result[key] for key in (
            "classification", "confidence", "duration_seconds", "sample_rate",
            "segments_analyzed", "total_detections",
        )},
    )
    db.add(analysis)
    db.flush()
    saved_detections = []
    for detection in result["detections"]:
        saved = AnalysisDetection(analysis_id=analysis.id, **detection)
        db.add(saved)
        saved_detections.append(saved)
    for score in result["segment_scores"]:
        db.add(AnalysisSegment(analysis_id=analysis.id, **score))
    db.commit()
    for saved, detection in zip(saved_detections, result["detections"]):
        detection["id"] = saved.id

    return DetectResponse(
        analysis_id=analysis.id,
        file=file.filename,
        threshold=threshold,
        model_version=metadata["model_version"],
        **result,
    )
