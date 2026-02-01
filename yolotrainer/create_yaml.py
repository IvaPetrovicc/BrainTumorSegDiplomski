import os
from pathlib import Path
import yaml

def find_data_yaml(dataset_dir: str) -> str:
    dataset_dir = Path(dataset_dir)
    top = dataset_dir / "data.yaml"
    if top.exists():
        return str(top)

    candidates = []
    for root, dirs, files in os.walk(dataset_dir):
        for f in files:
            if f.endswith(".yaml") or f.endswith(".yml"):
                candidates.append(Path(root) / f)

    if not candidates:
        raise FileNotFoundError("No .yaml data file found in dataset directory.")

    return str(candidates[0])

def override_class_names(data_yaml_path: str, new_names):
    data_yaml_path = Path(data_yaml_path)
    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["names"] = new_names
    data["nc"] = len(new_names)

    with open(data_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)

    print("Updated data.yaml with classes:", new_names)
    return str(data_yaml_path)
