import os
import pandas as pd
from fastapi import APIRouter
from typing import List
from ..schemas import Hydrophone

router = APIRouter()

DETECTIONS_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "processed", "detections.csv"
)

HYDROPHONE_DEFS = [
    {"name": "Dyes Inlet South", "lat": 47.6181, "lon": -122.6865, "color": "red"},
    {"name": "Dyes Inlet North", "lat": 47.6534, "lon": -122.6950, "color": "orange"},
    {"name": "Orcasound Lab - San Juan Island", "lat": 48.5583, "lon": -123.1650, "color": "blue"},
]


@router.get("", response_model=List[Hydrophone])
def get_hydrophones():
    results = []
    df = pd.DataFrame()
    if os.path.exists(DETECTIONS_CSV):
        df = pd.read_csv(DETECTIONS_CSV)

    for h in HYDROPHONE_DEFS:
        if not df.empty:
            loc_df = df[df["location"] == h["name"]]
            count = len(loc_df)
            avg_conf = round(float(loc_df["confidence"].mean()), 4) if count > 0 else 0.0
            last_date = str(loc_df["date"].max()) if count > 0 else None
        else:
            count = 0
            avg_conf = 0.0
            last_date = None

        results.append(
            Hydrophone(
                name=h["name"],
                lat=h["lat"],
                lon=h["lon"],
                color=h["color"],
                detection_count=count,
                avg_confidence=avg_conf,
                last_detection_date=last_date,
            )
        )
    return results
