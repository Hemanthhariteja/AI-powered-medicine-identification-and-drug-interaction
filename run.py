"""Run script for launching the Flask application.

Usage (PowerShell):
    python run.py

This script creates the Flask app via the application factory and starts
its development server. For production, use a WSGI server (gunicorn / waitress)
pointing at `src.app:create_app()`.
"""
from src.app import create_app

app = create_app()

if __name__ == "__main__":
    # Note: debug flag controlled by config DEBUG attribute.
    app.run(host="0.0.0.0", port=5000)
