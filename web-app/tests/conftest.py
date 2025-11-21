import os
import pytest
import mongomock
from werkzeug.security import generate_password_hash

os.environ["SECRET_KEY"] = "test-secret"

from app import create_app
from database import WebAppDatabase


@pytest.fixture
def app(monkeypatch):
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

    from database import db
    db.connect()  # reconnect after monkeypatch

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    return app


@pytest.fixture
def client(app):
    """pytest-flask fixture: provides test client"""
    return app.test_client()


@pytest.fixture
def logged_in_user(client):
    """Insert user + directly login through session cookie."""

    from database import db
    from werkzeug.security import generate_password_hash

    user_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "username": "testuser",
        "email": "user@test.com",
        "password_hash": generate_password_hash("anything")
    }

    db.users.insert_one(user_doc)
    with client: 
        with client.session_transaction() as sess:
            sess["_user_id"] = user_doc["_id"]
            sess["_fresh"] = True

    return user_doc