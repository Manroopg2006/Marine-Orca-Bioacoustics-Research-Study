import os
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from ..schemas import Detection, DetectionStats

router = APIRouter()

DETECTIONS_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "processed", "detections.csv"
)


def load_detections() -> pd.DataFrame:
    if not os.path.exists(DETECTIONS_CSV):
        return pd.DataFrame(columns=["start_sec", "end_sec", "confidence", "file", "location", "lat", "lon", "date"])
    df = pd.read_csv(DETECTIONS_CSV)
    df.index = df.index  # preserve original index
    return df


@router.get("", response_model=List[Detection])
def get_detections(
    location: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    df = load_detections()
    if df.empty:
        return []

    if location:
        df = df[df["location"].str.lower() == location.lower()]
    if min_confidence > 0:
        df = df[df["confidence"] >= min_confidence]

    df = df.iloc[offset : offset + limit].reset_index(drop=True)

    results = []
    for i, row in df.iterrows():
        results.append(
            Detection(
                id=int(i),
                start_sec=float(row["start_sec"]),
                end_sec=float(row["end_sec"]),
                confidence=float(row["confidence"]),
                file=str(row["file"]),
                location=str(row["location"]),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                date=str(row["date"]),
            )
        )
    return results


@router.get("/stats", response_model=DetectionStats)
def get_stats():
    df = load_detections()
    if df.empty:
        return DetectionStats(
            total=0,
            by_location={},
            avg_confidence=0.0,
            max_confidence=0.0,
            high_confidence_count=0,
            date_range={"min": "", "max": ""},
        )

    by_location = df.groupby("location").size().to_dict()
    return DetectionStats(
        total=len(df),
        by_location={str(k): int(v) for k, v in by_location.items()},
        avg_confidence=round(float(df["confidence"].mean()), 4),
        max_confidence=round(float(df["confidence"].max()), 4),
        high_confidence_count=int((df["confidence"] >= 0.9).sum()),
        date_range={
            "min": str(df["date"].min()),
            "max": str(df["date"].max()),
        },
    )


@router.get("/{detection_id}", response_model=Detection)
def get_detection(detection_id: int):
    df = load_detections()
    if detection_id < 0 or detection_id >= len(df):
        raise HTTPException(status_code=404, detail="Detection not found")
    row = df.iloc[detection_id]
    return Detection(
        id=detection_id,
        start_sec=float(row["start_sec"]),
        end_sec=float(row["end_sec"]),
        confidence=float(row["confidence"]),
        file=str(row["file"]),
        location=str(row["location"]),
        lat=float(row["lat"]),
        lon=float(row["lon"]),
        date=str(row["date"]),
    )
