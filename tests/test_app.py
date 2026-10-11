"""Tests for Flask app routes.

Uses the app factory to create a test client and validates HTTP responses.
"""
from __future__ import annotations
import pytest
from src.app import create_app

@pytest.fixture()
def client():
    app = create_app("testing")
    with app.test_client() as c:
        yield c

def test_index_ok(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Welcome" in resp.data

def test_identify_get_ok(client):
    resp = client.get("/identify")
    assert resp.status_code == 200
    assert b"Pill Identification" in resp.data
