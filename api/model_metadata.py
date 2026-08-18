"""Read model facts that are safe to show in the API and UI."""

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = PROJECT_ROOT / "model_metadata.json"


def get_model_metadata() -> dict[str, Any]:
    if not METADATA_PATH.exists():
        return {"model_version": "unknown", "threshold": 0.5}
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
