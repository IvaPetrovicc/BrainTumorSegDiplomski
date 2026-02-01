from typing import Optional
from pydantic import BaseModel


class TrainRequest(BaseModel):
    model_name: str
    epochs: int
    batch_size: int
    img_size: int
    device: str = "cpu"

    model_config = {"protected_namespaces": ()}


class TrainingMetrics(BaseModel):
    model_name: str
    epochs: int
    img_size: int
    batch_size: int
    device: str

    model_config = {"protected_namespaces": ()}


class TrainResponse(BaseModel):
    model_name: str
    epochs: int
    best_model_path: str
    metrics_path: str
    metrics: TrainingMetrics

    model_config = {"protected_namespaces": ()}


class PredictRequest(BaseModel):
    model_name: str
    image_path: str

    model_config = {"protected_namespaces": ()}


class PredictResponse(BaseModel):
    model_name: str
    prediction_path: str

    model_config = {"protected_namespaces": ()}


class PredictResult(BaseModel):
    filename: str
    model_used: str
    conf_th: float
    iou_th: float
    min_mask_area: int
    has_tumor: bool
    confidence: float
    description: str
    overlay_image: Optional[str] = None
    debug_info: Optional[dict] = None

    model_config = {"protected_namespaces": ()}


class ReportRequest(BaseModel):
    filename: str
    model_used: str
    conf_th: float
    iou_th: float
    min_mask_area: int
    has_tumor: bool
    confidence: float
    description: str = ""
    image_original: str
    image_overlay: Optional[str] = None

    model_config = {"protected_namespaces": ()}
