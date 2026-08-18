from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    classification: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)
    duration_seconds: Mapped[float] = mapped_column(Float)
    sample_rate: Mapped[int] = mapped_column(Integer)
    segments_analyzed: Mapped[int] = mapped_column(Integer)
    total_detections: Mapped[int] = mapped_column(Integer)
    threshold: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(64))
    detections: Mapped[list["AnalysisDetection"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )
    segment_scores: Mapped[list["AnalysisSegment"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class AnalysisDetection(Base):
    __tablename__ = "analysis_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    start_sec: Mapped[float] = mapped_column(Float)
    end_sec: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(String(32), nullable=True)
    feedback_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    analysis: Mapped[Analysis] = relationship(back_populates="detections")

class AnalysisSegment(Base):
    __tablename__ = "analysis_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True)
    start_sec: Mapped[float] = mapped_column(Float)
    end_sec: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    detected: Mapped[bool] = mapped_column(Boolean)
    analysis: Mapped[Analysis] = relationship(back_populates="segment_scores")
