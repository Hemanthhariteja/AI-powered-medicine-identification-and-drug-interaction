"""Input validation and error handling utilities."""
from __future__ import annotations
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from flask import current_app
import os


def validate_image_file(file: FileStorage | None) -> Tuple[bool, Optional[str]]:
    """Validate uploaded image file.
    
    Returns (is_valid, error_message).
    """
    if not file or file.filename == "":
        return False, "No file selected"
    
    filename = file.filename or ""
    if "." not in filename:
        return False, "File must have an extension"
    
    ext = filename.rsplit(".", 1)[1].lower()
    allowed = current_app.config.get("ALLOWED_IMAGE_EXTENSIONS", {"png", "jpg", "jpeg"})
    if ext not in allowed:
        return False, f"Unsupported file type. Allowed: {', '.join(allowed)}"
    
    # Check file size if seekable
    try:
        file.seek(0, os.SEEK_END)
        size_bytes = file.tell()
        file.seek(0)
        max_mb = current_app.config.get("MAX_FILE_SIZE_MB", 10)
        if size_bytes > max_mb * 1024 * 1024:
            return False, f"File too large. Max: {max_mb}MB"
    except Exception:
        pass  # Not all file-like objects are seekable
    
    return True, None


def validate_drug_name(name: str | None) -> Tuple[bool, Optional[str]]:
    """Validate drug name input."""
    if not name or not name.strip():
        return False, "Drug name is required"
    if len(name) > 200:
        return False, "Drug name too long (max 200 chars)"
    return True, None


def validate_confidence(confidence: float, threshold: float) -> Tuple[bool, str]:
    """Check if confidence meets threshold.
    
    Returns (is_acceptable, warning_message).
    """
    if confidence >= threshold:
        return True, ""
    return False, f"Low confidence ({confidence:.1%}). Consider manual verification."
