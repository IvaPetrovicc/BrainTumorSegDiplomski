import shutil
from pathlib import Path
import logging
import base64
import io
import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .schemas import TrainRequest, TrainResponse, PredictResult, ReportRequest
from .train_predict import train_model
from .models import registry
from .utils import safe_filename, dataset_ready, dataset_path, dataset_dir
from .routers import router as misc_router
from yolotrainer.custom_predictor import YoloPredictor
from parameters import (
    RESULTS_DIR,
    CUSTOM_MODEL_WEIGHTS,
    CONF_TH,
    IOU_TH,
    MIN_MASK_AREA,
    DEBUG,
    IMG_SIZE,
)

app = FastAPI(title="YOLOv12 Brain Tumor Segmentation API")
logger = logging.getLogger("backend")
DISPLAY_MODEL_NAME = "Brain MRI Segmentation"
PDF_FONT = "Helvetica"

def _init_pdf_font() -> None:
    global PDF_FONT
    candidates = [
        Path("C:/Windows/Fonts/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/Arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            name = path.stem
            pdfmetrics.registerFont(TTFont(name, str(path)))
            PDF_FONT = name
            return

_init_pdf_font()

def _decode_data_url(data_url: str) -> Image.Image | None:
    if not data_url:
        return None
    if "," in data_url:
        _, b64 = data_url.split(",", 1)
    else:
        b64 = data_url
    try:
        raw = base64.b64decode(b64)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None

def _draw_image_block(c: canvas.Canvas, title: str, image: Image.Image, y: float) -> float:
    page_w, page_h = A4
    margin = 50
    if image is None:
        return y

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, title)
    y -= 14

    max_w = page_w - margin * 2
    max_h = (page_h - margin * 2) / 2.2
    w, h = image.size
    scale = min(max_w / w, max_h / h, 1.0)
    draw_w = w * scale
    draw_h = h * scale

    if y - draw_h < margin:
        c.showPage()
        y = page_h - margin
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, title)
        y -= 14

    c.drawImage(ImageReader(image), margin, y - draw_h, width=draw_w, height=draw_h)
    return y - draw_h - 24


@app.get("/")
def root():
    return {"status": "FastAPI radi!", "message": "YOLO backend OK"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(misc_router)

@app.get("/health")
def health():
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except Exception:
        gpu_available = False
    try:
        model_names = getattr(registry.get("custom"), "names", None)
    except Exception:
        model_names = None

    return {
        "status": "ok",
        "models": ["custom"],
        "weights": {"custom": CUSTOM_MODEL_WEIGHTS},
        "model_status": {"custom": registry.status()},
        "model_names": model_names,
        "conf_th": CONF_TH,
        "iou_th": IOU_TH,
        "min_mask_area": MIN_MASK_AREA,
        "img_size": IMG_SIZE,
        "dataset_ready": dataset_ready(),
        "dataset_path": dataset_path(),
        "dataset_dir": dataset_dir(),
        "gpu_available": gpu_available,
    }

@app.post("/report")
def report_endpoint(req: ReportRequest):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    margin = 50
    y = page_h - margin

    c.setFont(PDF_FONT, 16)
    c.drawString(margin, y, "Izvještaj segmentacije")
    y -= 26

    c.setFont(PDF_FONT, 11)
    ts = datetime.datetime.now().strftime("%d.%m.%Y. %H:%M")
    lines = [
        f"Datum: {ts}",
        f"Datoteka: {req.filename}",
        f"Model: {req.model_used}",
        f"Tumor detektiran: {'Da' if req.has_tumor else 'Ne'}",
    ]
    for line in lines:
        c.drawString(margin, y, line)
        y -= 16

    original = _decode_data_url(req.image_original)
    overlay = _decode_data_url(req.image_overlay) if req.image_overlay else None

    if original and overlay:
        y -= 10
        max_w = (page_w - margin * 2 - 20) / 2
        max_h = (page_h - margin * 2) / 2.0
        ow, oh = original.size
        ow_scale = min(max_w / ow, max_h / oh, 1.0)
        ow_draw = ow * ow_scale
        oh_draw = oh * ow_scale
        vw, vh = overlay.size
        vw_scale = min(max_w / vw, max_h / vh, 1.0)
        vw_draw = vw * vw_scale
        vh_draw = vh * vw_scale

        row_h = max(oh_draw, vh_draw)
        if y - row_h < margin:
            c.showPage()
            y = page_h - margin

        c.setFont(PDF_FONT, 11)
        c.drawString(margin, y, "Izvorna slika")
        c.drawString(margin + max_w + 20, y, "Segmentacija")
        y -= 12
        c.drawImage(ImageReader(original), margin, y - oh_draw, width=ow_draw, height=oh_draw)
        c.drawImage(
            ImageReader(overlay),
            margin + max_w + 20,
            y - vh_draw,
            width=vw_draw,
            height=vh_draw,
        )
        y -= row_h + 10
    else:
        if original:
            y = _draw_image_block(c, "Izvorna slika", original, y)
        if overlay:
            y = _draw_image_block(c, "Segmentacija", overlay, y)

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    safe_name = safe_filename(req.filename)
    filename = f"izvjestaj_{safe_name or 'predikcija'}.pdf"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@app.post("/train", response_model=TrainResponse)
def train_endpoint(req: TrainRequest):
    if req.epochs < 1 or req.epochs > 500:
        raise HTTPException(status_code=400, detail="Epochs must be between 1 and 500.")
    if req.batch_size < 1 or req.batch_size > 128:
        raise HTTPException(status_code=400, detail="Batch size must be between 1 and 128.")
    if req.img_size < 64 or req.img_size > 2048:
        raise HTTPException(status_code=400, detail="Image size must be between 64 and 2048.")
    try:
        out = train_model(
            model_name=req.model_name,
            epochs=req.epochs,
            batch_size=req.batch_size,
            img_size=req.img_size,
            device=req.device,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TrainResponse(
        model_name=req.model_name,
        epochs=req.epochs,
        best_model_path=out["best_model_path"],
        metrics_path=out["metrics_path"],
        metrics=out["metrics"],
    )


@app.post("/predict", response_model=PredictResult)
async def predict_endpoint(
    model_choice: str = Form("custom"),
    conf_th: float = Form(None),
    iou_th: float = Form(None),
    file: UploadFile = File(...),
):
    if model_choice != "custom":
        raise HTTPException(status_code=400, detail="Only custom model is allowed for inference.")
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    tmp_dir = Path(RESULTS_DIR) / "uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    safe_name = safe_filename(file.filename)
    tmp_path = tmp_dir / safe_name

    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        model = registry.get("custom")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        predictor = YoloPredictor(model=model)
    except Exception as exc:  # pragma: no cover - simple construction check
        raise HTTPException(
            status_code=400,
            detail="Failed to initialize predictor.",
        ) from exc

    conf = CONF_TH if conf_th is None else float(conf_th)
    iou = IOU_TH if iou_th is None else float(iou_th)
    if conf < 0 or conf > 1:
        raise HTTPException(status_code=400, detail="conf_th must be between 0 and 1.")
    if iou < 0 or iou > 1:
        raise HTTPException(status_code=400, detail="iou_th must be between 0 and 1.")

    logger.info(
        "predict model=custom weights_used=%s model_names=%s",
        registry.loaded_weights,
        getattr(model, "names", None),
    )

    try:
        has_tumor, conf_out, result, debug_info = predictor.predict_tumor_binary(
            str(tmp_path),
            img_size=IMG_SIZE,
            conf_th=conf,
            iou_th=iou,
            min_mask_area=MIN_MASK_AREA,
            retina_masks=True,
            max_det=50,
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    overlay_b64 = predictor.render_overlay_base64(result)
    overlay_image = f"data:image/png;base64,{overlay_b64}" if overlay_b64 else None

    mask_count = debug_info.get("mask_count") if debug_info else None
    avg_mask_area = debug_info.get("avg_mask_area") if debug_info else None
    top_conf = debug_info.get("max_confidence_tumor") if debug_info else None
    logger.info(
        "predict params conf=%.3f iou=%.3f mask_count=%s avg_mask_area=%s top_conf=%s file=%s",
        conf,
        iou,
        mask_count,
        avg_mask_area,
        top_conf,
        safe_name,
    )

    if has_tumor:
        description = f"Tumor detected with confidence {conf_out:.3f}."
    else:
        description = (
            f"No tumor detected. Highest tumor-class confidence was {conf_out:.3f}. "
            "If you expect a positive case, verify model weights."
        )

    if DEBUG and debug_info:
        logger.info(
            "predict_debug model=%s raw=%s tumor_before=%s removed_area=%s removed_class=%s max_conf=%.4f max_tumor=%.4f class_idx=%s classes_present=%s",
        "custom",
        debug_info.get("raw_detections"),
        debug_info.get("tumor_detections_before_filter"),
        debug_info.get("removed_by_min_area"),
            debug_info.get("removed_by_class"),
            debug_info.get("max_confidence_raw"),
            debug_info.get("max_confidence_tumor"),
            debug_info.get("tumor_class_idx"),
            debug_info.get("classes_present"),
        )

    return PredictResult(
        filename=safe_name,
        model_used=DISPLAY_MODEL_NAME,
        conf_th=conf,
        iou_th=iou,
        min_mask_area=MIN_MASK_AREA,
        has_tumor=has_tumor,
        confidence=conf_out,
        description=description,
        overlay_image=overlay_image,
        debug_info=debug_info if DEBUG else None,
    )


# Provide /api/* aliases for convenience / proxies.
app.add_api_route("/api/health", health, methods=["GET"])
app.add_api_route("/api/train", train_endpoint, methods=["POST"], response_model=TrainResponse)
app.add_api_route("/api/predict", predict_endpoint, methods=["POST"], response_model=PredictResult)
app.add_api_route("/api/report", report_endpoint, methods=["POST"])
