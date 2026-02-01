"""Simple CLI to train YOLO model without FastAPI."""
import argparse
from backend.app.train_predict import train_model
from parameters import IMG_SIZE, BATCH_SIZE, EPOCHS

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="custom", choices=["custom"])
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch", type=int, default=BATCH_SIZE)
    parser.add_argument("--img", type=int, default=IMG_SIZE)
    parser.add_argument("--device", type=str, default="cpu", help="Device string passed to Ultralytics (e.g., cpu, 0)")
    args = parser.parse_args()

    out = train_model(
        model_name=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img,
        device=args.device,
    )
    print("Training finished.")
    print("Best model:", out["best_model_path"])
