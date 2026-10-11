"""Pill predictor using a trained Keras model.

Loads a saved `.keras` model and associated `*_labels.json` mapping.
Provides a `predict_topk` method returning top-K predictions.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import json

import numpy as np
import tensorflow as tf
import keras


@dataclass
class Prediction:
    label: str
    score: float


class PillPredictor:
    def __init__(self, model_path: str | Path):
        model_path = Path(model_path)
        labels_path = model_path.with_name(model_path.stem + "_labels.json")
        assert labels_path.exists(), f"Labels file not found: {labels_path}"
        self.labels: List[str] = json.loads(labels_path.read_text())["class_names"]
        self.model = keras.models.load_model(model_path)
        # Determine input size from model
        self.img_size = tuple(self.model.input_shape[1:3])  # type: ignore[union-attr]  # (H, W)

    def _load_and_preprocess(self, image_path: str | Path) -> np.ndarray:
        img_bytes = tf.io.read_file(str(image_path))
        img = tf.image.decode_image(img_bytes, channels=3, expand_animations=False)
        img = tf.image.convert_image_dtype(img, tf.float32)
        img = tf.image.resize(img, self.img_size)
        # MobileNetV2 preprocess
        img = keras.applications.mobilenet_v2.preprocess_input(img)
        return img.numpy()  # type: ignore[return-value]

    def predict_topk(self, image_path: str | Path, k: int = 3) -> List[Prediction]:
        x = self._load_and_preprocess(image_path)
        x = np.expand_dims(x, 0)
        probs = self.model.predict(x, verbose=0)[0]  # type: ignore[union-attr]
        topk_idx = np.argsort(probs)[::-1][:k]
        return [Prediction(self.labels[i], float(probs[i])) for i in topk_idx]
