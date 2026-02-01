import os
from roboflow import Roboflow
from parameters import (
    ROBOFLOW_API_KEY,
    ROBOFLOW_WORKSPACE,
    ROBOFLOW_PROJECT,
    ROBOFLOW_VERSION,
    ROBOFLOW_FORMAT,
    DATASET_DIR,
)

def download_dataset_if_needed() -> str:
    # If data.yaml already exists inside DATASET_DIR, assume dataset is ready
    for root, dirs, files in os.walk(DATASET_DIR):
        for f in files:
            if f.endswith(".yaml") or f.endswith(".yml"):
                return DATASET_DIR

    print("Dataset not found locally. Downloading from Roboflow...")
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT)
    version = project.version(ROBOFLOW_VERSION)
    dataset = version.download(ROBOFLOW_FORMAT)
    print("Dataset downloaded to:", dataset.location)
    return dataset.location
