import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const backendUrl = process.env.API_URL || "http://127.0.0.1:8000";
const imagePath =
  process.env.IMAGE_PATH ||
  path.resolve(__dirname, "..", "Brain-Tumor-Segmentation-1", "train", "images", "Tr-no_0530_jpg.rf.9e490ab3c4795a63d61e48186c7bd5db.jpg");

async function run() {
  const fileBuffer = fs.readFileSync(imagePath);
  const form = new FormData();
  const filename = path.basename(imagePath);
  const ext = path.extname(filename).toLowerCase();
  const mime =
    ext === ".png" ? "image/png" : ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "application/octet-stream";
  const file = new Blob([fileBuffer], { type: mime });
  form.append("model_choice", "custom");
  form.append("file", file, filename);

  const res = await fetch(`${backendUrl}/predict`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  const data = await res.json();

  const required = [
    "filename",
    "model_used",
    "conf_th",
    "iou_th",
    "min_mask_area",
    "has_tumor",
    "confidence",
    "overlay_image",
  ];
  const missing = required.filter((key) => !(key in data));
  if (missing.length) {
    throw new Error(`Missing keys: ${missing.join(", ")}`);
  }

  console.log("OK custom", {
    model_used: data.model_used,
    has_tumor: data.has_tumor,
    confidence: data.confidence,
  });
}

await run();
