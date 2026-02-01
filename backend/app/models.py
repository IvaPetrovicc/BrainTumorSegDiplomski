from typing import Dict, Optional
from pathlib import Path
from ultralytics import YOLO
from parameters import CUSTOM_MODEL_WEIGHTS

class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, YOLO] = {}
        self.last_error: Optional[str] = None
        self.loaded_weights: Optional[str] = None

    def _resolve_custom_weights(self) -> str:
        path = Path(CUSTOM_MODEL_WEIGHTS)
        if path.exists():
            return str(path)
        raise FileNotFoundError(
            "Custom model weights missing. Set CUSTOM_MODEL_WEIGHTS or place best.pt in project root."
        )

    def get(self, name: str = "custom") -> YOLO:
        if name != "custom":
            raise ValueError("Only 'custom' model is allowed for inference.")
        if "custom" in self.models:
            return self.models["custom"]
        resolved = self._resolve_custom_weights()
        model = YOLO(resolved)
        self.models["custom"] = model
        self.loaded_weights = resolved
        self.last_error = None
        return model

    def status(self) -> Dict[str, Optional[str]]:
        try:
            self.get("custom")
            return {"ok": True, "error": None, "weights_used": self.loaded_weights}
        except Exception as exc:
            msg = str(exc)
            self.last_error = msg
            return {"ok": False, "error": msg, "weights_used": None}

registry = ModelRegistry()
