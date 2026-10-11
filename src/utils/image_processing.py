"""Image loading and preprocessing utilities.

Replace the placeholder logic with robust pipelines:
- Resize / normalization
- Color space conversions
- Augmentations (during training)
"""
from __future__ import annotations
from typing import Any
from pathlib import Path
from PIL import Image
import numpy as np


def load_image(path: str | Path) -> Image.Image:
    """Load an image from disk.

    Parameters
    ----------
    path : str | Path
        Filesystem path to the image file.

    Returns
    -------
    PIL.Image.Image
        Loaded image object.
    """
    return Image.open(path).convert("RGB")

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess image into a NumPy array suitable for model inference.

    Steps (placeholder):
    - Resize to 224x224
    - Convert to NumPy array
    - Normalize to [0,1]

    Parameters
    ----------
    image : PIL.Image.Image
        Input image.

    Returns
    -------
    np.ndarray
        Preprocessed image array.
    """
    image = image.resize((224, 224))
    arr = np.asarray(image, dtype=np.float32) / 255.0
    return arr
