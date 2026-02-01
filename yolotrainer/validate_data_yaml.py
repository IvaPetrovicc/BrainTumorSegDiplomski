from __future__ import annotations

from pathlib import Path
import yaml


def validate_or_fix_data_yaml(data_yaml_path: str, expected_names: list[str]) -> bool:
    """
    Validate (and if needed rewrite) data.yaml to match expected class names.
    Returns True if the file matches after validation.
    """
    path = Path(data_yaml_path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    current_names = data.get("names", [])
    current_nc = data.get("nc")
    expected_nc = len(expected_names)

    needs_write = current_names != expected_names or current_nc != expected_nc
    if needs_write:
        print(
            "WARNING: data.yaml class schema mismatch. "
            f"Found nc={current_nc}, names={current_names}. "
            f"Expected nc={expected_nc}, names={expected_names}. Rewriting."
        )
        data["names"] = expected_names
        data["nc"] = expected_nc
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)
    else:
        print("data.yaml class schema OK.")

    return True


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate or fix YOLO data.yaml schema.")
    parser.add_argument("data_yaml", type=str, help="Path to data.yaml")
    parser.add_argument(
        "--names",
        nargs="+",
        default=["meningioma", "notumor"],
        help="Class names in order",
    )
    args = parser.parse_args()

    validate_or_fix_data_yaml(args.data_yaml, args.names)


if __name__ == "__main__":
    main()
