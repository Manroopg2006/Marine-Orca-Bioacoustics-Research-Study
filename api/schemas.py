from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional, List, Dict


class Detection(BaseModel):
    id: int
    start_sec: float
    end_sec: float
    confidence: float
    file: str
    location: str
    lat: float
    lon: float
    date: str


class DetectionStats(BaseModel):
    total: int
    by_location: Dict[str, int]
    avg_confidence: float
    max_confidence: float
    high_confidence_count: int
    date_range: Dict[str, str]


class Hydrophone(BaseModel):
    name: str
    lat: float
    lon: float
    color: str
    detection_count: int
    avg_confidence: float
    last_detection_date: Optional[str]


class SpectrogramInfo(BaseModel):
    filename: str
    url: str
    title: str


class DetectRequest(BaseModel):
    file_path: str
    location: str
    lat: float
    lon: float
    date: str


class DetectResponse(BaseModel):
    analysis_id: int
    file: str
    classification: str
    confidence: float
    duration_seconds: float
    sample_rate: int
    segments_analyzed: int
    total_detections: int
    threshold: float
    model_version: str
    detections: List[Dict]
    segment_scores: List[Dict]


class FeedbackRequest(BaseModel):
    feedback: str


class AnalysisSummary(BaseModel):
    id: int
    file: str
    created_at: datetime
    classification: str
    confidence: float
    duration_seconds: float
    sample_rate: int
    segments_analyzed: int
    total_detections: int
    threshold: float
    model_version: str


class AnalysisDetail(AnalysisSummary):
    detections: List[Dict]


class ModelMetadata(BaseModel):
    model_version: str
    training_date: str
    dataset_version: str
    available_recordings_used: int
    missing_labeled_recordings: int
    feature_type: str
    classifier: str
    segment_duration_seconds: int
    threshold: float
    threshold_selection: str
    test_metrics: Dict[str, Any]
    known_limitations: List[str]
