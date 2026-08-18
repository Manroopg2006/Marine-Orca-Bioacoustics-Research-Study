import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..model_metadata import get_model_metadata
from ..models import Analysis, AnalysisDetection
from ..schemas import AnalysisDetail, AnalysisSummary, FeedbackRequest, ModelMetadata


router = APIRouter()
VALID_FEEDBACK = {"confirmed_orca", "false_positive", "unsure"}
PUBLIC_HISTORY_ENABLED = os.getenv("PUBLIC_HISTORY_ENABLED", "false").lower() == "true"


def serialize_detection(detection: AnalysisDetection) -> dict:
    return {
        "id": detection.id,
        "start_sec": detection.start_sec,
        "end_sec": detection.end_sec,
        "confidence": detection.confidence,
        "feedback": detection.feedback,
    }


def serialize_analysis(analysis: Analysis, include_detections: bool = False) -> dict:
    data = {
        "id": analysis.id,
        "file": analysis.file_name,
        "created_at": analysis.created_at,
        "classification": analysis.classification,
        "confidence": analysis.confidence,
        "duration_seconds": analysis.duration_seconds,
        "sample_rate": analysis.sample_rate,
        "segments_analyzed": analysis.segments_analyzed,
        "total_detections": analysis.total_detections,
        "threshold": analysis.threshold,
        "model_version": analysis.model_version,
    }
    if include_detections:
        data["detections"] = [serialize_detection(item) for item in analysis.detections]
    return data


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(limit: int = 10, db: Session = Depends(get_db)):
    if not PUBLIC_HISTORY_ENABLED:
        raise HTTPException(status_code=404, detail="Public analysis history is disabled")
    limit = min(max(limit, 1), 50)
    rows = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()
    return [serialize_analysis(row) for row in rows]


@router.post("/detections/{detection_id}/feedback")
def save_feedback(detection_id: int, payload: FeedbackRequest, db: Session = Depends(get_db)):
    if payload.feedback not in VALID_FEEDBACK:
        raise HTTPException(status_code=400, detail="Feedback must be confirmed_orca, false_positive, or unsure")
    detection = db.get(AnalysisDetection, detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    detection.feedback = payload.feedback
    detection.feedback_at = datetime.utcnow()
    db.commit()
    db.refresh(detection)
    return serialize_detection(detection)


@router.get("/model/metadata", response_model=ModelMetadata)
def model_metadata():
    return get_model_metadata()


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    if not PUBLIC_HISTORY_ENABLED:
        raise HTTPException(status_code=404, detail="Public analysis history is disabled")
    analysis = (
        db.query(Analysis)
        .options(selectinload(Analysis.detections))
        .filter(Analysis.id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return serialize_analysis(analysis, include_detections=True)
