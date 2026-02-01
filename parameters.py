import os
from pathlib import Path

# Roboflow configuration for brain tumor dataset
ROBOFLOW_API_KEY = "BXOxgJCfCCiJVclYO5f2"
ROBOFLOW_WORKSPACE = "fpmoz"
ROBOFLOW_PROJECT = "brain-tumor-segmentation-jteuo-vwha2"
ROBOFLOW_VERSION = 1
ROBOFLOW_FORMAT = "yolov8"

                

# YOLO weights (custom tumor model only for inference)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BEST = Path(PROJECT_ROOT) / "best.pt"
CUSTOM_MODEL_WEIGHTS = os.getenv("CUSTOM_MODEL_WEIGHTS", str(DEFAULT_BEST))

# Training parameters
IMG_SIZE = 256
BATCH_SIZE = 8
EPOCHS = 50
LEARNING_RATE = 1e-3
SEED = 42

# Inference parameters (aggressive defaults for higher recall)
INFER_IMG_SIZE = int(os.getenv("INFER_IMG_SIZE", "1024"))
CONF_TH = float(os.getenv("CONF_TH", "0.01"))
IOU_TH = float(os.getenv("IOU_TH", "0.30"))
MIN_MASK_AREA = int(os.getenv("MIN_MASK_AREA", "0"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

# Paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def _find_local_dataset_dir() -> str | None:
    root = Path(PROJECT_ROOT)
    candidates = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if (entry / "data.yaml").exists() and (entry / "train" / "images").exists():
            candidates.append(entry)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.name.lower())
    return str(candidates[0])


DEFAULT_DATASET_DIR = _find_local_dataset_dir() or DATA_DIR
DATASET_DIR = os.getenv("DATASET_DIR", DEFAULT_DATASET_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

for d in [DATA_DIR, RESULTS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)
