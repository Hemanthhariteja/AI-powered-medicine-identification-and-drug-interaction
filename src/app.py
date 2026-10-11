"""Flask application factory.

Refactored to register frontend and API blueprints defined in
`src.routes`. This keeps `app.py` slim and focused on initialization:
 - Configuration loading
 - Extension initialization
 - Blueprint registration
 - Simple error handlers
"""
from __future__ import annotations
from flask import Flask, jsonify
import os
from config import get_config
from src.utils.database import init_db, db
from src.routes import frontend_bp, api_bp


def create_app(config_name: str | None = None) -> Flask:
    """Application factory.

    Parameters
    ----------
    config_name : str | None
        Optional configuration name (development/testing/production).
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    cfg_cls = get_config(config_name)
    app.config.from_object(cfg_cls)

    # Initialize extensions
    init_db(app)

    # Ensure upload folder exists
    os.makedirs(app.config["IMAGE_UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints
    app.register_blueprint(frontend_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Error handlers returning JSON for API routes
    @app.errorhandler(404)
    def not_found(e):  # noqa: D401
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):  # noqa: D401
        return jsonify({"error": "Internal server error"}), 500

    @app.cli.command("init-db")
    def init_db_command():  # pragma: no cover - manual CLI usage
        """Initialize database tables."""
        with app.app_context():
            db.create_all()
            print("Database initialized.")

    return app

__all__ = ["create_app"]
