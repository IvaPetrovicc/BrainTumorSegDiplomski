import argparse
from pathlib import Path

from parameters import CUSTOM_MODEL_WEIGHTS, IMG_SIZE, MIN_MASK_AREA
from yolotrainer.custom_predictor import YoloPredictor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=str, help="Path to image for debug grid.")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    predictor = YoloPredictor(weights_path=CUSTOM_MODEL_WEIGHTS)

    conf_values = [0.05, 0.10, 0.15, 0.20]
    iou_values = [0.40, 0.50, 0.60]

    print(f"Image: {image_path}")
    print(f"Weights: {CUSTOM_MODEL_WEIGHTS}")
    print("conf\tiou\tmasks\tavg_area\ttop_conf")
    for conf in conf_values:
        for iou in iou_values:
            has_tumor, top_conf, _result, debug_info = predictor.predict_tumor_binary(
                str(image_path),
                img_size=IMG_SIZE,
                conf_th=conf,
                iou_th=iou,
                min_mask_area=MIN_MASK_AREA,
                retina_masks=True,
                max_det=50,
            )
            mask_count = debug_info.get("mask_count", 0)
            avg_mask_area = debug_info.get("avg_mask_area", 0)
            print(f"{conf:.2f}\t{iou:.2f}\t{mask_count}\t{avg_mask_area}\t{top_conf:.3f}")


if __name__ == "__main__":
    main()
