from pydantic import BaseModel
from typing import Optional, List, Dict


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
    file: str
    location: str
    total_detections: int
    detections: List[Dict]
