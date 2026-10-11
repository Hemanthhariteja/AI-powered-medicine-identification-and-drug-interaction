"""Database initialization utilities.

Provides a SQLAlchemy instance bound to the Flask app. This separation
allows importing `db` across modules without circular dependencies.
"""
from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# Global SQLAlchemy object; initialized via init_db(app)
db = SQLAlchemy()

def init_db(app: Flask) -> None:
    """Initialize SQLAlchemy with app context.

    Parameters
    ----------
    app : Flask
        Flask application instance.
    """
    db.init_app(app)
