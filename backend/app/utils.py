import os
import datetime
import json
from pathlib import Path
from typing import Dict, Any
from parameters import RESULTS_DIR, DATA_DIR, DATASET_DIR

def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def experiment_dir(model_name: str) -> str:
    t = timestamp()
    path = Path(RESULTS_DIR) / f"{model_name}_{t}"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def save_metrics(metrics: Dict[str, Any], out_dir: str) -> str:
    path = Path(out_dir) / "metrics.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return str(path)

def safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", "."))

def dataset_dir() -> str:
    """Return preferred dataset directory (env DATASET_DIR or default DATA_DIR)."""
    return DATASET_DIR

def dataset_ready() -> bool:
    """Dataset is ready if data.yaml exists and train/images is present."""
    data_yaml = dataset_path()
    if data_yaml is None:
        return False
    train_images = Path(dataset_dir()) / "train" / "images"
    return train_images.exists()

def dataset_path() -> str | None:
    """Return the first found data.yaml path in DATASET_DIR or fallback DATA_DIR."""
    for root, _, files in os.walk(DATASET_DIR):
        for f in files:
            if f.endswith((".yaml", ".yml")):
                return str(Path(root) / f)
    for root, _, files in os.walk(DATA_DIR):
        for f in files:
            if f.endswith((".yaml", ".yml")):
                return str(Path(root) / f)
    return None
