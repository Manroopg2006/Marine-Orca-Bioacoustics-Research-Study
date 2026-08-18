import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .routers import detections, hydrophones, spectrograms, audio, analyses
from .database import init_db

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="OrcaPath AI",
    description="REST API for orca call detection and analysis",
    version="1.0.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",") + [
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
app.include_router(analyses.router, prefix="/api/analyses", tags=["analyses"])


@app.get("/api")
def api_root():
    return {
        "name": "OrcaPath AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


# In Docker, the React production build is copied here so one service can
# serve both the public site and its API. API routes are registered first.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
