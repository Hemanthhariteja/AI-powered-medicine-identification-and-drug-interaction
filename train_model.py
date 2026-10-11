"""Standalone model training entry point.

This script demonstrates how to invoke the training routine from
`src.models.model_training` to produce a model artifact stored under
`models/trained_models/`.

Usage (PowerShell):
    python train_model.py --epochs 5 --output pill_classifier.pt

In real scenarios, integrate dataset loading, augmentation, and
hyperparameter management.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from src.models.model_training import train_pill_model
from config import get_config

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train pill identification model")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs per phase (default: 50)")
    parser.add_argument("--output", type=str, default="pill_mobilenetv2.keras", help="Model filename")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    cfg = get_config()
    output_path = Path(cfg.MODEL_STORAGE_PATH) / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = train_pill_model(epochs_frozen=args.epochs, epochs_finetune=args.epochs)
    # Placeholder for saving torch model or sklearn pipeline
    try:
        import torch  # type: ignore[import-not-found]
        torch.save(result.model.state_dict(), output_path)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Torch save failed: {exc}. Saving placeholder text.")
        output_path.write_text("MODEL_PLACEHOLDER")

    print("Training complete.")
    print("Metrics:", result.metrics)
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
