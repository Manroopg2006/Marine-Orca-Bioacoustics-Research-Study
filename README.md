# OrcaPath AI

Upload-first web app for detecting possible orca (killer whale) vocalizations in underwater WAV recordings. It classifies audio into small segments and returns a simple Orca / No Orca result, confidence score, and detected timestamps.

## Current app

The public-facing app is intentionally simple:

1. A video-backed **Orca Detector** landing page scrolls to the upload form.
2. A user uploads one WAV file (maximum 50 MB).
3. FastAPI runs the trained classifier over 1-second segments.
4. The result shows the highest confidence, audio duration, sample rate, number of analyzed segments, and any possible-call timestamps.

### Add the landing video

Download a licensed MP4 from [Pexels' orca video collection](https://www.pexels.com/search/videos/orca/) and save it as `frontend/public/media/orca-hero.mp4`. Record its creator and exact URL in `frontend/public/media/README.md`. The interface has a visual fallback if no video is present.

---

## How it works

```
WAV upload → FastAPI validation → 1-second audio windows
    → log-Mel features → Random Forest classifier → PostgreSQL results
    → React audio player and interactive confidence timeline
```

Each recording is resampled to 44.1 kHz and split into one-second windows. Each window becomes 128-bin log-Mel spectrogram summary features (up to 20 kHz). The trained Random Forest returns an orca-call probability for every second; the chosen threshold determines whether that second is shown as a possible call.

---

## Project structure

```
orcapath-ai/
├── main.py                        # ML training pipeline
├── download_data.py               # DagsHub dataset downloader
├── requirements_api.txt           # Backend dependencies
│
├── src/
│   ├── audio/
│   │   ├── spectrogram.py         # Mel spectrogram generation
│   │   ├── extract_calls.py       # Extract labeled orca call features
│   │   ├── extract_negatives.py   # Extract no-orca chunk features
│   │   ├── extract_all_calls.py   # Batch feature extraction
│   │   └── combine_datasets.py    # Merge Orcasound + Watkins datasets
│   ├── models/
│   │   ├── detect.py              # Run detection on new recordings
│   │   ├── cluster.py             # K-means cluster validation
│   │   ├── call_clustering.py     # Orca call type clustering
│   │   ├── temporal_analysis.py   # Transition matrix + permutation test
│   │   └── orca_detector.pkl      # Trained model (not committed)
│   └── visualization/
│       └── map.py                 # Folium detection heatmap
│
├── api/
│   ├── main.py                    # FastAPI app
│   ├── schemas.py                 # Pydantic request/response models
│   └── routers/
│       ├── detections.py          # GET /api/detections, /stats
│       ├── hydrophones.py         # GET /api/hydrophones
│       ├── spectrograms.py        # GET /api/spectrograms, generate endpoint
│       └── audio.py               # POST /api/audio/detect (WAV upload)
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Dashboard.tsx      # Main layout
│       │   ├── StatsPanel.tsx     # 4 summary stat cards
│       │   ├── DetectionFeed.tsx  # Filterable detection list
│       │   ├── DetectionCard.tsx  # Individual detection card
│       │   ├── SpectrogramViewer.tsx  # Detection detail + spectrogram PNG
│       │   └── ConfidenceChart.tsx    # Detections by location bar chart
│       ├── api/client.ts          # Axios API client
│       └── types/index.ts         # Shared TypeScript types
│
└── data/
    ├── raw_audio/                 # WAV files (not committed)
    └── processed/                 # detections.csv, PNGs (not committed)
```

---

## Datasets

| Dataset | Location | Dates | Files |
|---|---|---|---|
| Orcasound Lab | San Juan Island, WA | Sept 2017, July 2019 | ~10 WAV |
| ONC Digby | Dyes Inlet, Puget Sound | Oct 1997 | 2 WAV |
| Watkins Marine Mammal | Reference library | Various | 70 clips |

Hydrophone coordinates:
- **Dyes Inlet South** — 47.6181, -122.6865
- **Dyes Inlet North** — 47.6534, -122.6950
- **Orcasound Lab, San Juan Island** — 48.5583, -123.1650

---

## Setup

### 1. Clone and install Python dependencies

```bash
git clone <repo-url>
cd orcapath-ai
pip install -r requirements_api.txt
```

> Also install ML training dependencies if running the pipeline:
> `pip install librosa scikit-learn pandas numpy matplotlib folium joblib`

### 2. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running the ML pipeline

> Requires audio files in `data/raw_audio/` and labeled `.txt` files alongside them.

```bash
# Train the classifier
python main.py

# Run detection on recordings (edit file paths in detect.py first)
python -m src.models.detect

# Cluster call types
python -m src.models.call_clustering

# Temporal pattern analysis
python -m src.models.temporal_analysis

# Generate interactive map
python -m src.visualization.map
```

Outputs land in `data/processed/`:
- `detections.csv` — all timestamped detections with coordinates
- `orca_detector.pkl` — serialized trained model
- `*.png` — spectrogram and analysis plots
- `orca_map.html` — standalone Folium detection map

---

## Running the dashboard

### Start the backend

```bash
cd orcapath-ai
python -m uvicorn api.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### Start the frontend

```bash
cd frontend
npm run dev
```

Dashboard available at `http://localhost:5173`

The Vite dev server proxies all `/api` requests to `:8000` automatically.

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/detections` | List detections — filter by `location`, `min_confidence`, `limit` |
| GET | `/api/detections/stats` | Aggregate stats (total, by location, avg confidence) |
| GET | `/api/detections/{id}` | Single detection by index |
| GET | `/api/hydrophones` | All hydrophone stations with detection counts |
| GET | `/api/spectrograms` | List available spectrogram PNGs |
| GET | `/api/spectrograms/{filename}` | Serve a spectrogram PNG |
| POST | `/api/spectrograms/generate` | Generate spectrogram for a WAV segment on the fly |
| GET | `/api/audio/files` | List available WAV files in the project |
| POST | `/api/audio/detect` | Upload a WAV file and run detection |

---

## Model details

| Parameter | Value |
|---|---|
| Algorithm | RandomForestClassifier |
| Estimators | 100 trees |
| Input features | Flattened mel spectrogram — 54,528 dimensions |
| Chunk duration | 5 seconds |
| Sample rate | 44,100 Hz |
| Mel bins | 128 |
| Frequency range | 0 – 20,000 Hz |
| Output | Binary (0 = no orca, 1 = orca) + probability |
| Train/test split | 80 / 20 |
| Class balancing | Upsample minority class |

---

## What is not committed to git

```
data/raw_audio/          # WAV files — large binaries
data/processed/*.csv     # Detection results
data/processed/*.npy     # Feature arrays
data/processed/*.png     # Generated plots
data/processed/*.html    # Folium map
src/models/*.pkl         # Trained model weights
frontend/node_modules/
frontend/dist/
```
# Orca Detector

## Persistent analysis history

Every upload now creates an analysis record with the file name, time, model version, threshold, and detected timestamps. You can label a detected segment as **Confirmed orca**, **False positive**, or **Unsure**. Those labels are stored as review data; they do not change the model automatically.

For the simplest local run, the API creates `data/orcapath.db` with SQLite. To run the app and PostgreSQL together with Docker, use:

```powershell
docker compose up --build
```

Then open `http://localhost:8080`. Stop it with `docker compose down`; the named PostgreSQL volume preserves your analysis history.

The current model's documented evaluation and limitations are in [MODEL_CARD.md](MODEL_CARD.md). Its machine-readable facts are available at `/api/analyses/model/metadata`.

## Deploy the web app on Render

The repository includes a Render Blueprint at `render.yaml`. It builds the existing Dockerfile, which compiles the React site and serves it from the FastAPI app on one web service.

1. Make sure `src/models/orca_detector.pkl` is present. It is the trained Random Forest model required for audio uploads. The repository's `.gitignore` now allows this specific model file to be committed; other generated model files remain ignored.
2. Commit and push the deployment files and model to the Git repository you want Render to use.
3. In Render, choose **New > Blueprint**, connect that repository, and apply the `render.yaml` configuration. Render will build and deploy the web service.
4. When deployment finishes, open the service's `onrender.com` URL. Check `/api/health` for `{"status":"ok"}`, then use the upload page to try a WAV file.

This starter setup uses the app's default SQLite database. On a host without persistent storage, saved analysis records can disappear when the service is restarted or redeployed. Public analysis history stays disabled by default. If you want records and feedback to persist, configure a persistent disk or a hosted PostgreSQL database before relying on them.
