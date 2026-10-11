"""Data loading utilities for pill image datasets using TensorFlow.

Dataset expectation:
- A single root directory with subfolders per class, containing images.
  Example:
    data/pills_dataset/
      aspirin/
        img1.jpg
      ibuprofen/
        img2.jpg

This module will split the files into train/val/test sets and build
`tf.data.Dataset` pipelines with preprocessing and optional augmentation.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

AUTOTUNE = tf.data.AUTOTUNE

@dataclass
class DatasetSplits:
    train: tf.data.Dataset
    val: tf.data.Dataset
    test: tf.data.Dataset
    class_names: List[str]


def _gather_image_paths(data_dir: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Return arrays of image paths and numeric labels and the class names list."""
    data_dir = Path(data_dir)
    class_names = sorted([d.name for d in data_dir.iterdir() if d.is_dir()])
    image_paths: List[str] = []
    labels: List[int] = []
    for idx, cls in enumerate(class_names):
        for p in (data_dir / cls).glob("**/*"):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
                image_paths.append(str(p))
                labels.append(idx)
    return np.array(image_paths), np.array(labels), class_names


def _decode_and_resize(path: tf.Tensor, img_size: Tuple[int, int]) -> tf.Tensor:
    """Read file, decode image, resize, and scale to [0,1]."""
    img_bytes = tf.io.read_file(path)
    img = tf.image.decode_image(img_bytes, channels=3, expand_animations=False)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, img_size)
    return img


def _augment_image(img: tf.Tensor, seed: tf.Tensor | None = None) -> tf.Tensor:  # type: ignore[return]
    """Apply brightness augmentation using tf.image.random_brightness.

    Other augmentations (flip/rotation/zoom) are handled via Keras layers in the model.
    """
    delta = 0.1  # brightness range
    if seed is None:
        img = tf.image.random_brightness(img, max_delta=delta)  # type: ignore[assignment]
    else:
        img = tf.image.stateless_random_brightness(img, max_delta=delta, seed=seed)  # type: ignore[assignment]
    return tf.clip_by_value(img, 0.0, 1.0)  # type: ignore[return-value]


def build_datasets(
    data_dir: str | Path,
    img_size: Tuple[int, int] = (224, 224),
    batch_size: int = 32,
    val_split: float = 0.15,
    test_split: float = 0.15,
    seed: int = 42,
    augment_brightness: bool = True,
) -> DatasetSplits:
    """Create train/val/test datasets from a folder-of-folders dataset.

    Splits are stratified to respect class distributions.
    For very small datasets, reduces split sizes to ensure minimum samples per class.
    """
    paths, labels, class_names = _gather_image_paths(Path(data_dir))
    assert len(paths) > 0, f"No images found under: {data_dir}"
    
    num_classes = len(class_names)
    samples_per_class = len(paths) // num_classes
    
    # Adjust splits for very small datasets to ensure minimum samples per class
    if samples_per_class <= 5:
        # For tiny datasets, use fixed number of samples per split
        # Need at least num_classes samples in test set for stratification
        test_samples = num_classes  # 1 per class
        val_samples = num_classes   # 1 per class
        test_split = test_samples / len(paths)
        val_split = val_samples / (len(paths) - test_samples)

    # Train/val/test split (stratified)
    x_temp, x_test, y_temp, y_test = train_test_split(
        paths, labels, test_size=test_split, random_state=seed, stratify=labels
    )
    val_ratio = val_split / (1.0 - test_split)
    x_train, x_val, y_train, y_val = train_test_split(
        x_temp, y_temp, test_size=val_ratio, random_state=seed, stratify=y_temp
    )

    def make_ds(x: np.ndarray, y: np.ndarray, shuffle: bool) -> tf.data.Dataset:
        ds = tf.data.Dataset.from_tensor_slices((x, y))
        if shuffle:
            ds = ds.shuffle(buffer_size=len(x), seed=seed, reshuffle_each_iteration=True)
        def _load(path, label):
            img = _decode_and_resize(path, img_size)
            if augment_brightness and shuffle:
                img = _augment_image(img)
            return img, tf.cast(label, tf.int32)
        ds = ds.map(_load, num_parallel_calls=AUTOTUNE)
        return ds.batch(batch_size).prefetch(AUTOTUNE)

    train_ds = make_ds(x_train, y_train, shuffle=True)
    val_ds = make_ds(x_val, y_val, shuffle=False)
    test_ds = make_ds(x_test, y_test, shuffle=False)

    return DatasetSplits(train=train_ds, val=val_ds, test=test_ds, class_names=class_names)
