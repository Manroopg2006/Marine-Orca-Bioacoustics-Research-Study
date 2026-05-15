import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import detections, hydrophones, spectrograms, audio

app = FastAPI(
    title="OrcaPath AI",
    description="REST API for orca call detection and analysis",
    version="1.0.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detections.router, prefix="/api/detections", tags=["detections"])
app.include_router(hydrophones.router, prefix="/api/hydrophones", tags=["hydrophones"])
app.include_router(spectrograms.router, prefix="/api/spectrograms", tags=["spectrograms"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])


@app.get("/")
def root():
    return {
        "name": "OrcaPath AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
