"""General helper functions for the Flask application.

Currently houses convenience utilities for:
- Validating file extensions
- Standard JSON response formatting
You can expand this module with logging, authentication helpers, etc.
"""
from __future__ import annotations
from typing import Iterable, Dict, Any

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def json_success(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": True, **data}

def json_error(message: str, **extra: Any) -> Dict[str, Any]:
    return {"success": False, "error": message, **extra}
