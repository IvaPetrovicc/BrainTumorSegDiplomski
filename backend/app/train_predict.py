from pathlib import Path
from typing import Dict, Any
from ultralytics import YOLO

from parameters import RESULTS_DIR, CUSTOM_MODEL_WEIGHTS
from yolotrainer.build_data import prepare_yolo_data
from .utils import experiment_dir, save_metrics

MODEL_WEIGHTS = {
    "custom": CUSTOM_MODEL_WEIGHTS,
}

def train_model(
    model_name: str,
    epochs: int,
    batch_size: int,
    img_size: int,
    device: str = "cpu",
) -> Dict[str, Any]:
    if model_name not in MODEL_WEIGHTS:
        raise ValueError(f"Unsupported model_name '{model_name}'. Use one of: {list(MODEL_WEIGHTS.keys())}")

    exp_dir = experiment_dir(model_name)
    classes = ["meningioma", "notumor"]
    data_yaml = prepare_yolo_data(classes=classes)

    weights_path = MODEL_WEIGHTS[model_name]
    try:
        model = YOLO(weights_path)
    except Exception as exc:
        raise ValueError(
            f"Failed to load weights '{weights_path}'. Ensure the file exists or can be downloaded."
        ) from exc

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        project=exp_dir,
        name="train",
        device=device,
        verbose=False,
    )

    best_model_path = Path(exp_dir) / "train" / "weights" / "best.pt"

    metrics = {
        "model_name": model_name,
        "epochs": epochs,
        "img_size": img_size,
        "batch_size": batch_size,
        "device": device,
    }

    metrics_path = save_metrics(metrics, exp_dir)

    return {
        "experiment_dir": exp_dir,
        "best_model_path": str(best_model_path),
        "metrics": metrics,
        "metrics_path": metrics_path,
    }
