"""TensorFlow/Keras training with MobileNetV2 for pill identification.

This module provides a complete training pipeline using transfer learning:
- Loads images from class subfolders
- Splits into train/val/test
- Applies augmentation (flip, rotation, zoom, brightness)
- Freezes base for warmup, then fine-tunes upper layers
- Saves model and labels
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json

import numpy as np
import tensorflow as tf
import keras
from keras import layers

from src.utils.data_loader import build_datasets
from src.utils.metrics import compute_metrics
from config import get_config


IMG_SIZE = (299, 299)  # Larger for better feature extraction
BATCH_SIZE = 16  # Increased batch size for better gradient estimates


def build_augmentation() -> keras.Sequential:
    """Return a Keras augmentation pipeline.

    Enhanced augmentation with translation and increased ranges
    for better generalization and reduced overfitting.
    """
    return keras.Sequential(
        [
            layers.RandomFlip("horizontal_and_vertical"),
            layers.RandomRotation(0.3),  # Increased
            layers.RandomZoom(0.3),  # Increased
            layers.RandomTranslation(0.2, 0.2),  # Added translation
            layers.RandomContrast(0.3),  # Increased
            layers.RandomBrightness(0.3),  # Increased
        ],
        name="augmentation",
    )


def build_model(num_classes: int) -> keras.Model:
    """Create a MobileNetV2-based classifier with enhanced architecture.
    
    Improvements:
    - Larger dense layers (256, 128)
    - Additional BatchNormalization
    - Progressive dropout (0.5 -> 0.4 -> 0.3)
    """
    base = keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False

    inputs = layers.Input(shape=(*IMG_SIZE, 3))
    x = build_augmentation()(inputs)
    x = keras.applications.mobilenet_v2.preprocess_input(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    # First dense layer with more neurons
    x = layers.Dense(512, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    # Second dense layer
    x = layers.Dense(256, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    # Third dense layer for deeper features
    x = layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01))(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    model = keras.Model(inputs, outputs, name="pill_mobilenetv2")
    return model


@dataclass
class TrainResult:
    model: keras.Model
    history_frozen: Any
    history_ft: Any
    metrics: Dict[str, Any]
    labels: List[str]


def train_pill_model(
    data_root: str | Path | None = None,
    output_name: str = "pill_mobilenetv2.keras",
    epochs_frozen: int = 50,  # Increased from 5 to 50
    epochs_finetune: int = 50,  # Increased from 5 to 50
    fine_tune_at: int = 100,  # Changed from 120 to 100
    seed: int = 42,
) -> TrainResult:
    """Train MobileNetV2 transfer learning model and save artifacts.

    Parameters
    ----------
    data_root : str | Path | None
        Root folder with class subdirectories. Defaults to data/pills_dataset.
    output_name : str
        Model filename to write under models/trained_models.
    epochs_frozen : int
        Epochs with base frozen (warm-up training).
    epochs_finetune : int
        Epochs after unfreezing top layers for fine-tuning.
    fine_tune_at : int
        Unfreeze from this layer index in the base model.
    seed : int
        Random seed for shuffling.
    """
    cfg = get_config()
    if data_root is None:
        data_root = Path("data") / "pills_dataset"
    data_root = Path(data_root)
    out_dir = Path(cfg.MODEL_STORAGE_PATH)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build datasets (brightness augmentation occurs only for training)
    splits = build_datasets(
        data_dir=data_root, img_size=IMG_SIZE, batch_size=BATCH_SIZE, seed=seed
    )
    class_names = splits.class_names
    num_classes = len(class_names)

    model = build_model(num_classes)
    
    # Use higher initial learning rate with cosine decay
    initial_lr = 1e-3
    model.compile(
        optimizer=keras.optimizers.Adam(initial_lr),  # type: ignore[arg-type]
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=False),
        metrics=["accuracy"],
    )

    # Calculate class weights to handle imbalance
    y_train = np.concatenate([y for x, y in splits.train], axis=0)
    class_counts = np.bincount(y_train.astype(int))
    total_samples = len(y_train)
    class_weights = {i: total_samples / (num_classes * count) for i, count in enumerate(class_counts)}  # type: ignore[misc]
    
    # Cosine annealing learning rate schedule
    cosine_decay = keras.callbacks.CosineAnnealingScheduler(
        T_max=epochs_frozen,
        eta_min=1e-6,
        verbose=0
    ) if hasattr(keras.callbacks, 'CosineAnnealingScheduler') else keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-7,
        verbose=1
    )
    
    # Enhanced callbacks for better training
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=15,
        restore_best_weights=True,
        min_delta=0.005,  # type: ignore[arg-type]
        mode='max'
    )
    
    # Save best model checkpoint
    checkpoint_path = out_dir / f"checkpoint_{output_name}"
    checkpoint = keras.callbacks.ModelCheckpoint(
        str(checkpoint_path),
        monitor='val_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    )

    history_frozen = model.fit(
        splits.train,
        validation_data=splits.val,
        epochs=epochs_frozen,
        class_weight=class_weights,
        callbacks=[early_stop, cosine_decay, checkpoint],
        verbose=1
    )

    # Fine-tune: unfreeze more layers for better feature learning
    base = model.get_layer(index=2)  # inputs(0), augmentation(1), base(2)
    assert isinstance(base, keras.Model) or hasattr(base, "layers")
    base.trainable = True  # type: ignore[union-attr]
    # Unfreeze from layer 50 for more aggressive fine-tuning
    actual_fine_tune = min(fine_tune_at, 50)  # Unfreeze more layers
    for layer in base.layers[:actual_fine_tune]:  # type: ignore[union-attr]
        layer.trainable = False

    # Cosine decay for fine-tuning phase
    cosine_decay_ft = keras.callbacks.CosineAnnealingScheduler(
        T_max=epochs_finetune,
        eta_min=1e-7,
        verbose=0
    ) if hasattr(keras.callbacks, 'CosineAnnealingScheduler') else keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-8,
        verbose=1
    )

    model.compile(
        optimizer=keras.optimizers.Adam(5e-5),  # type: ignore[arg-type]  # Higher LR for fine-tuning
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=False),
        metrics=["accuracy"],
    )
    history_ft = model.fit(
        splits.train,
        validation_data=splits.val,
        epochs=epochs_finetune,
        class_weight=class_weights,
        callbacks=[early_stop, cosine_decay_ft, checkpoint],
        verbose=1
    )

    # Evaluate
    y_true: List[int] = []
    y_pred: List[int] = []
    test_dataset = splits.test
    for batch_imgs, batch_labels in test_dataset:  # type: ignore[misc]
        probs = model.predict(batch_imgs, verbose=0)  # type: ignore[arg-type]
        preds = np.argmax(probs, axis=1)
        y_pred.extend(preds.tolist())
        y_true.extend(batch_labels.numpy().tolist())
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    metrics = compute_metrics(y_true_arr, y_pred_arr, class_names)

    # Save model and labels
    model_path = out_dir / output_name
    labels_path = out_dir / (Path(output_name).stem + "_labels.json")
    model.save(model_path)
    labels_path.write_text(json.dumps({"class_names": class_names}, indent=2))

    return TrainResult(
        model=model,
        history_frozen=history_frozen.history,
        history_ft=history_ft.history,
        metrics=metrics,
        labels=class_names,
    )
