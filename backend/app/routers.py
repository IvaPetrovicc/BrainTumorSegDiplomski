"""
Lightweight router helpers to keep main.py clean.
"""
from fastapi import APIRouter, HTTPException

from yolotrainer.utils import download_dataset_if_needed

router = APIRouter()


@router.post("/dataset/download")
def trigger_dataset_download():
    """
    Download the Roboflow dataset if missing and return the local path.
    """
    try:
        path = download_dataset_if_needed()
    except Exception as exc:  # pragma: no cover - just surfacing errors
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"dataset_path": path}
