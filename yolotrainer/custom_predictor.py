import base64
import io
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO


class YoloPredictor:
    def __init__(self, weights_path: Optional[str] = None, model: Optional[YOLO] = None):
        if model is None and not weights_path:
            raise ValueError("Provide either an initialized YOLO model or a weights_path.")
        self.model = model or YOLO(weights_path)

    @staticmethod
    def _normalize_class_name(name: str) -> str:
        return str(name).strip().lower().replace("_", "").replace("-", "").replace(" ", "")

    def _resolve_tumor_class_idx(self, default_idx: int = 0) -> int:
        names = getattr(self.model, "names", None)
        indexed_names = {}
        if isinstance(names, dict):
            for idx, name in names.items():
                try:
                    indexed_names[int(idx)] = self._normalize_class_name(name)
                except Exception:
                    continue
        elif isinstance(names, list):
            indexed_names = {idx: self._normalize_class_name(name) for idx, name in enumerate(names)}

        if not indexed_names:
            return default_idx

        tumor_aliases = {"tumor", "meningioma"}
        non_tumor_aliases = {"notumor", "healthy", "normal", "background"}

        for idx, name in indexed_names.items():
            if name in tumor_aliases:
                return idx

        # If this is a binary model and one class clearly means "no tumor",
        # use the other class as the positive tumor class.
        if len(indexed_names) == 2:
            non_tumor_ids = {idx for idx, name in indexed_names.items() if name in non_tumor_aliases}
            if len(non_tumor_ids) == 1:
                for idx in indexed_names:
                    if idx not in non_tumor_ids:
                        return idx

        if default_idx in indexed_names:
            return default_idx
        return sorted(indexed_names.keys())[0]

    def predict_image(
        self,
        image_path: str,
        img_size: int = 256,
        conf_th: float = 0.25,
        iou_th: float = 0.7,
        retina_masks: bool = True,
        max_det: int = 50,
    ):
        results = self.model.predict(
            source=image_path,
            imgsz=img_size,
            conf=conf_th,
            iou=iou_th,
            retina_masks=retina_masks,
            max_det=max_det,
            save=False,
            verbose=False,
            task="segment",
        )
        return results[0]

    def predict_tumor_binary(
        self,
        image_path: str,
        img_size: int = 256,
        conf_th: float = 0.25,
        iou_th: float = 0.7,
        min_mask_area: int = 200,
        retina_masks: bool = True,
        max_det: int = 50,
    ):
        tumor_class_idx = self._resolve_tumor_class_idx(default_idx=0)
        res = self.predict_image(
            image_path,
            img_size=img_size,
            conf_th=conf_th,
            iou_th=iou_th,
            retina_masks=retina_masks,
            max_det=max_det,
        )
        has_tumor = False
        best_conf = 0.0
        max_conf = 0.0
        raw_count = int(len(res.boxes)) if res.boxes is not None else 0
        tumor_count_before = 0
        removed_by_area = 0
        removed_by_class = 0
        tumor_count_after = 0
        mask_areas = []

        # Prefer segmentation masks if present.
        if res.masks is not None and res.boxes is not None and len(res.boxes) > 0:
            masks = res.masks.data
            for i, b in enumerate(res.boxes):
                cls_id = int(b.cls.item())
                conf = float(b.conf.item())
                if conf > max_conf:
                    max_conf = conf
                if cls_id != tumor_class_idx:
                    removed_by_class += 1
                    continue
                tumor_count_before += 1
                if min_mask_area > 0 and masks is not None and i < len(masks):
                    mask = masks[i]
                    area = int((mask > 0.5).sum().item())
                    if area < min_mask_area:
                        removed_by_area += 1
                        continue
                    mask_areas.append(area)
                tumor_count_after += 1
                if conf > best_conf:
                    best_conf = conf
                    has_tumor = True
        elif res.boxes is not None and len(res.boxes) > 0:
            for b in res.boxes:
                cls_id = int(b.cls.item())
                conf = float(b.conf.item())
                if conf > max_conf:
                    max_conf = conf
                if cls_id != tumor_class_idx:
                    removed_by_class += 1
                    continue
                tumor_count_before += 1
                if conf > best_conf:
                    best_conf = conf
                    has_tumor = True
                tumor_count_after += 1

        classes_present = []
        if res.boxes is not None and len(res.boxes) > 0:
            try:
                classes_present = sorted({int(c) for c in res.boxes.cls.tolist()})
            except Exception:
                classes_present = []

        avg_mask_area = int(sum(mask_areas) / len(mask_areas)) if mask_areas else 0

        debug_info = {
            "raw_detections": raw_count,
            "tumor_detections_before_filter": tumor_count_before,
            "removed_by_min_area": removed_by_area,
            "removed_by_class": removed_by_class,
            "tumor_detections_after_filter": tumor_count_after,
            "max_confidence_raw": max_conf,
            "max_confidence_tumor": best_conf,
            "mask_count": len(mask_areas),
            "avg_mask_area": avg_mask_area,
            "tumor_class_idx": tumor_class_idx,
            "model_names": getattr(self.model, "names", None),
            "classes_present": classes_present,
        }

        return has_tumor, best_conf, res, debug_info

    def render_overlay_base64(self, result) -> Optional[str]:
        """
        Render the YOLO result with boxes/masks and return a base64 PNG string.
        """
        if result is None or result.orig_img is None:
            return None

        # Start from the original image to ensure consistent styling.
        base_bgr = result.orig_img
        img = Image.fromarray(base_bgr[..., ::-1]).convert("RGBA")  # BGR -> RGBA

        def _class_name(cls_id: int) -> str:
            names = getattr(self.model, "names", None)
            if isinstance(names, dict):
                return str(names.get(int(cls_id), "")).lower()
            if isinstance(names, list) and int(cls_id) < len(names):
                return str(names[int(cls_id)]).lower()
            return ""

        def _is_meningioma(cls_id: int) -> bool:
            return _class_name(cls_id) == "meningioma"

        red_rgba = (255, 0, 0, 120)
        blue_rgba = (30, 144, 255, 120)
        red_rgb = (255, 0, 0, 255)
        blue_rgb = (30, 144, 255, 255)

        # Overlay segmentation masks with per-class color (tumor red, others blue).
        if result.masks is not None and result.masks.data is not None and result.boxes is not None:
            masks = result.masks.data
            try:
                masks = masks.cpu().numpy()
            except Exception:
                masks = np.asarray(masks)

            try:
                classes = result.boxes.cls.cpu().tolist()
            except Exception:
                classes = result.boxes.cls.tolist()

            for i, mask in enumerate(masks):
                mask_bool = mask > 0.5
                if not mask_bool.any():
                    continue
                cls_id = int(classes[i]) if i < len(classes) else 0
                color = red_rgba if _is_meningioma(cls_id) else blue_rgba
                overlay = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
                overlay[mask_bool] = color
                overlay_img = Image.fromarray(overlay, "RGBA")
                img = Image.alpha_composite(img, overlay_img)

        # Draw bounding boxes with per-class color and label (class + conf).
        if result.boxes is not None and len(result.boxes) > 0:
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            try:
                boxes = result.boxes.xyxy.cpu().tolist()
                classes = result.boxes.cls.cpu().tolist()
                confs = result.boxes.conf.cpu().tolist()
            except Exception:
                boxes = result.boxes.xyxy.tolist()
                classes = result.boxes.cls.tolist()
                confs = result.boxes.conf.tolist()
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box
                cls_id = int(classes[i]) if i < len(classes) else 0
                outline = red_rgb if _is_meningioma(cls_id) else blue_rgb
                draw.rectangle([x1, y1, x2, y2], outline=outline, width=3)

                conf = float(confs[i]) if i < len(confs) else 0.0
                label = _class_name(cls_id) or str(cls_id)
                text = f"{label} {conf:.2f}"
                if hasattr(draw, "textbbox"):
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                elif hasattr(font, "getbbox"):
                    bbox = font.getbbox(text)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                else:
                    tw, th = font.getsize(text)
                tx = max(0, int(x1))
                ty = max(0, int(y1) - th - 4)
                draw.rectangle([tx, ty, tx + tw + 4, ty + th + 4], fill=(0, 0, 0, 160))
                draw.text((tx + 2, ty + 2), text, fill=(255, 255, 255, 255), font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")
