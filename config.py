"""Application configuration module.

This module centralizes configuration settings for different environments
(Development, Testing, Production). It reads environment variables when
present, providing sane defaults for local development.

Attributes
---------
Config : class
    Base configuration with defaults.
DevelopmentConfig : class
    Development overrides (debug settings).
TestingConfig : class
    Testing overrides (use in-memory / separate DB).
ProductionConfig : class
    Production overrides (tighter settings).
get_config : function
    Helper to retrieve the appropriate config class by name.
"""
from __future__ import annotations
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models" / "trained_models"
DATA_DIR = BASE_DIR / "data"

class Config:
    """Base configuration shared across environments."""
    APP_NAME: str = "Medicine AI System"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'medicine.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False
    # ML / model related
    MODEL_STORAGE_PATH: str = MODELS_DIR.as_posix()
    IMAGE_UPLOAD_FOLDER: str = (DATA_DIR / "raw_images").as_posix()
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
    MIN_CONFIDENCE_THRESHOLD: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.5"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    
    # API settings
    RXNAV_API_TIMEOUT: int = int(os.getenv("RXNAV_API_TIMEOUT", "10"))
    ENABLE_API_FALLBACK: bool = os.getenv("ENABLE_API_FALLBACK", "true").lower() == "true"
    
    # Session settings
    SESSION_TYPE: str = "filesystem"
    SESSION_PERMANENT: bool = False
    PERMANENT_SESSION_LIFETIME: int = int(os.getenv("SESSION_LIFETIME", "3600"))  # 1 hour

class DevelopmentConfig(Config):
    """Development settings (verbose logging, easier debugging)."""
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True

class TestingConfig(Config):
    """Testing settings (uses in-memory SQLite)."""
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"

class ProductionConfig(Config):
    """Production settings (stricter)"""
    DEBUG: bool = False
    TESTING: bool = False
    MIN_CONFIDENCE_THRESHOLD: float = 0.6
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

def get_config(name: str | None = None) -> type[Config]:
    """Return a configuration class based on name.

    Parameters
    ----------
    name : str | None
        Name of the desired configuration (development/testing/production).
        If None or not found, defaults to development.
    """
    if not name:
        name = os.getenv("FLASK_ENV", "development")
    return CONFIG_MAP.get(name.lower(), DevelopmentConfig)
