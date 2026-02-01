import argparse
import random
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def resolve_train_images(data_yaml: Path):
    data = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    train = data.get("train")
    if not train:
        raise ValueError("data.yaml missing 'train' entry.")

    base = data_yaml.parent
    paths = []

    def add_path(p):
        if isinstance(p, (list, tuple)):
            for item in p:
                add_path(item)
            return
        p = str(p)
        has_glob = any(ch in p for ch in ["*", "?", "["])
        if has_glob:
            root = Path(p)
            if not root.is_absolute():
                root = base / root
            paths.extend(root.parent.glob(root.name))
            return
        path = Path(p)
        if not path.is_absolute():
            path = base / path
        paths.append(path)

    add_path(train)

    images = []
    for p in paths:
        if p.is_dir():
            for ext in IMG_EXTS:
                images.extend(p.rglob(f"*{ext}"))
        elif p.is_file() and p.suffix.lower() in IMG_EXTS:
            images.append(p)
    return images


def resolve_expected_class_ids(data: dict) -> set[int]:
    names = data.get("names", [])
    if isinstance(names, dict):
        out = set()
        for key in names.keys():
            try:
                out.add(int(key))
            except Exception:
                continue
        return out
    if isinstance(names, list):
        return set(range(len(names)))
    nc = data.get("nc")
    try:
        return set(range(int(nc)))
    except Exception:
        return {0}


def label_path_for_image(img_path: Path) -> Path:
    parts = list(img_path.parts)
    if "images" in parts:
        idx = parts.index("images")
        parts[idx] = "labels"
        return Path(*parts).with_suffix(".txt")
    return img_path.with_suffix(".txt")


def draw_polygons(img_path: Path, polygons, out_path: Path):
    img = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for poly in polygons:
        if len(poly) < 3:
            continue
        draw.polygon(poly, outline=(255, 0, 0, 255), fill=(255, 0, 0, 60))

    out = Image.alpha_composite(img, overlay).convert("RGB")
    out.save(out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/data.yaml")
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_yaml = Path(args.data)
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml not found: {data_yaml}")

    data = yaml.safe_load(data_yaml.read_text(encoding="utf-8")) or {}
    expected_class_ids = resolve_expected_class_ids(data)
    images = resolve_train_images(data_yaml)
    if not images:
        raise RuntimeError("No training images found.")

    random.seed(args.seed)
    sample = random.sample(images, k=min(args.samples, len(images)))

    debug_dir = Path("debug_overlays")
    debug_dir.mkdir(parents=True, exist_ok=True)

    empty_labels = 0
    bad_class = 0
    bad_format = 0
    out_of_range = 0

    for img_path in sample:
        label_path = label_path_for_image(img_path)
        if not label_path.exists() or label_path.stat().st_size == 0:
            empty_labels += 1
            continue

        polygons = []
        lines = label_path.read_text(encoding="utf-8").strip().splitlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 3:
                bad_format += 1
                continue
            try:
                cls_id = int(float(parts[0]))
                coords = [float(x) for x in parts[1:]]
            except Exception:
                bad_format += 1
                continue

            if cls_id not in expected_class_ids:
                bad_class += 1
                continue

            if len(coords) % 2 != 0:
                bad_format += 1
                continue

            if any(c < 0.0 or c > 1.0 for c in coords):
                out_of_range += 1
                continue

            w, h = Image.open(img_path).size
            pts = []
            for i in range(0, len(coords), 2):
                x = coords[i] * w
                y = coords[i + 1] * h
                pts.append((x, y))
            polygons.append(pts)

        if polygons:
            out_path = debug_dir / img_path.name
            draw_polygons(img_path, polygons, out_path)

    print("Sanity check complete")
    print(f"Checked samples: {len(sample)}")
    print(f"Empty/missing labels: {empty_labels}")
    print(f"Bad class IDs (expected {sorted(expected_class_ids)}): {bad_class}")
    print(f"Bad format lines: {bad_format}")
    print(f"Coords out of [0,1]: {out_of_range}")
    print(f"Overlays saved to: {debug_dir.resolve()}")


if __name__ == "__main__":
    main()
