"""
Pytest configuration and fixtures for the web app test suite.

This module provides:
- Mock MongoDB client using mongomock
- Flask test client fixtures
- Pre-authenticated user fixture for protected routes
"""

import os

# Set environment variables before importing app modules
os.environ["SECRET_KEY"] = "test-secret"

# pylint: disable=wrong-import-position
import pytest
import mongomock
from werkzeug.security import generate_password_hash

from app import create_app
from database import WebAppDatabase, db

# pylint: enable=wrong-import-position


@pytest.fixture(name="application")
def fixture_application(monkeypatch):
    """Use pytest-flask 'app' fixture pattern."""
    # Patch DB to use mongomock
    mock_client = mongomock.MongoClient()

    def fake_connect(self):
        self.client = mock_client
        self.db = mock_client["test_db"]
        self.users = self.db["users"]
        self.receipts = self.db["receipts"]
        return True

    monkeypatch.setattr(WebAppDatabase, "connect", fake_connect)

    db.connect()  # reconnect after monkeypatch

    application = create_app()
    application.config["TESTING"] = True
    application.config["SECRET_KEY"] = "test-secret"

    return application


@pytest.fixture(name="client")
def fixture_client(application):
    """pytest-flask fixture: provides test client."""
    return application.test_client()


@pytest.fixture(name="logged_in_user")
def fixture_logged_in_user(client):
    """Insert user + directly login through session cookie."""
    user_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "username": "testuser",
        "email": "user@test.com",
        "password_hash": generate_password_hash("anything"),
    }

    db.users.insert_one(user_doc)

    with client:
        with client.session_transaction() as sess:
            sess["_user_id"] = user_doc["_id"]
            sess["_fresh"] = True

    return user_doc
