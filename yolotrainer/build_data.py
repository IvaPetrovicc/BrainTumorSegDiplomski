from .utils import download_dataset_if_needed
from .create_yaml import find_data_yaml, override_class_names
from .validate_data_yaml import validate_or_fix_data_yaml

def prepare_yolo_data(classes=None):
    """Ensure dataset is downloaded from Roboflow and data.yaml is configured."""
    ds_dir = download_dataset_if_needed()
    data_yaml = find_data_yaml(ds_dir)
    if classes is not None:
        data_yaml = override_class_names(data_yaml, classes)
    if classes is not None:
        validate_or_fix_data_yaml(data_yaml, classes)
    return data_yaml
