import argparse
import shutil
from pathlib import Path

import yaml

NOTUMOR_NAMES = {"notumor", "no_tumor", "no-tumor", "no tumor", "background"}


def resolve_path(base: Path, p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (base / path)


def convert_label_file(label_path: Path, notumor_ids: set[int]) -> int:
    if not label_path.exists():
        return 0
    lines = label_path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return 0
    out_lines = []
    removed = 0
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        try:
            cls_id = int(float(parts[0]))
        except ValueError:
            continue
        if cls_id in notumor_ids:
            removed += 1
            continue
        parts[0] = "0"
        out_lines.append(" ".join(parts))
    label_path.write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/data.yaml")
    parser.add_argument("--out", type=str, default="data_single")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    data_yaml = Path(args.data)
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml not found: {data_yaml}")

    src_root = data_yaml.parent.resolve()
    out_root = Path(args.out).resolve()
    if out_root.exists():
        if not args.overwrite:
            raise FileExistsError(f"Output exists: {out_root}. Use --overwrite to replace it.")
        shutil.rmtree(out_root)
    shutil.copytree(src_root, out_root)

    out_yaml = out_root / data_yaml.name
    data = yaml.safe_load(out_yaml.read_text(encoding="utf-8"))
    names = data.get("names", [])

    notumor_ids = set()
    if isinstance(names, dict):
        for k, v in names.items():
            if str(v).strip().lower() in NOTUMOR_NAMES:
                notumor_ids.add(int(k))
    elif isinstance(names, list):
        for idx, name in enumerate(names):
            if str(name).strip().lower() in NOTUMOR_NAMES:
                notumor_ids.add(idx)

    train_path = resolve_path(out_root, str(data.get("train")))
    val_path = resolve_path(out_root, str(data.get("val")))
    test_path = resolve_path(out_root, str(data.get("test"))) if data.get("test") else None

    label_dirs = []
    for p in [train_path, val_path, test_path]:
        if not p:
            continue
        if p.is_dir():
            label_dirs.append(p.parent / "labels")

    removed_total = 0
    for label_dir in label_dirs:
        if not label_dir.exists():
            continue
        for label_path in label_dir.rglob("*.txt"):
            removed_total += convert_label_file(label_path, notumor_ids)

    data["nc"] = 1
    data["names"] = ["tumor"]
    out_yaml.write_text(yaml.safe_dump(data), encoding="utf-8")

    print(f"Converted dataset written to: {out_root}")
    print(f"Removed notumor labels: {removed_total}")
    print(f"Updated data.yaml: nc=1, names=['tumor']")


if __name__ == "__main__":
    main()
