from fastapi.testclient import TestClient
from types import SimpleNamespace

from api.database import SessionLocal
from api.main import app
from api.models import AnalysisSegment


def fake_analysis(_: str, threshold_override: float | None = None) -> dict:
    return {
        "classification": "orca",
        "confidence": 0.91,
        "duration_seconds": 1.0,
        "sample_rate": 44_100,
        "segments_analyzed": 1,
        "total_detections": 1,
        "detections": [{"start_sec": 0.0, "end_sec": 1.0, "confidence": 0.91}],
        "segment_scores": [{
            "start_sec": 0.0,
            "end_sec": 1.0,
            "confidence": 0.91,
            "detected": True,
        }],
    }


def test_upload_persists_analysis_and_feedback(monkeypatch):
    monkeypatch.setattr("src.models.detect.analyze_audio", fake_analysis)
    monkeypatch.setattr(
        "api.routers.audio.sf.info",
        lambda _: SimpleNamespace(format="WAV", frames=44_100, samplerate=44_100),
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/audio/detect",
            data={"threshold": "0.75"},
            files={"file": ("fixture.wav", b"tiny test audio", "audio/wav")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["classification"] == "orca"
        assert body["analysis_id"] > 0
        assert body["threshold"] == 0.75
        assert body["detections"][0]["id"] > 0
        assert body["segment_scores"][0]["confidence"] == 0.91

        with SessionLocal() as db:
            segment_count = db.query(AnalysisSegment).filter_by(analysis_id=body["analysis_id"]).count()
        assert segment_count == 1

        feedback = client.post(
            f"/api/analyses/detections/{body['detections'][0]['id']}/feedback",
            json={"feedback": "confirmed_orca"},
        )
        assert feedback.status_code == 200
        assert feedback.json()["feedback"] == "confirmed_orca"


def test_rejects_non_wav_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/audio/detect",
            files={"file": ("notes.txt", b"not sound", "text/plain")},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only WAV files are supported"


def test_rejects_invalid_wav_content():
    with TestClient(app) as client:
        response = client.post(
            "/api/audio/detect",
            files={"file": ("not-really-audio.wav", b"not a WAV header", "audio/wav")},
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is not a readable WAV recording."


def test_exposes_model_metadata():
    with TestClient(app) as client:
        response = client.get("/api/analyses/model/metadata")
    assert response.status_code == 200
    assert response.json()["model_version"] == "random-forest-log-mel-v1"
    assert response.json()["test_metrics"]["confusion_matrix"] == [[928, 472], [920, 697]]


def test_public_analysis_history_is_disabled():
    with TestClient(app) as client:
        response = client.get("/api/analyses")
    assert response.status_code == 404
