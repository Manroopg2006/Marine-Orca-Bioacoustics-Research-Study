# Train the CNN in Google Colab

1. In Google Drive, create `My Drive/OrcaPath/`.
2. Upload these folders into it:
   - `Marine-Orca-Bioacoustics-Research-Study/` with the current source code. Do not include `.venv`, `frontend/node_modules`, `frontend/dist`, or `data/raw_audio/orcasound`.
   - `orcasound/` with `train.csv`, `test.csv`, and the audio folders you downloaded.
3. Upload and open `notebooks/train_cnn_colab.ipynb` in [Google Colab](https://colab.research.google.com/).
4. Select **Runtime > Change runtime type > T4 GPU**, then run all cells from top to bottom.
5. Download the generated `orca_cnn.pt` and `cnn_training_metrics.json` from `My Drive/OrcaPath/cnn_output/`.

To use the returned model locally, copy it to `src/models/orca_cnn.pt` and set the backend before starting FastAPI:

```powershell
$env:ORCA_MODEL_BACKEND = "cnn"
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

The app defaults to the Random Forest unless `ORCA_MODEL_BACKEND=cnn` is set, so you can compare models safely.

Google Colab already supplies GPU-enabled PyTorch. For local CPU CNN use, install `requirements_cnn.txt` instead of only `requirements_api.txt`.
