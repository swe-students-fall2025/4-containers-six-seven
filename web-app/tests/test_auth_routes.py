"""
Tests for authentication routes: signup, login, and /me endpoint.
"""


def test_signup(client):
    """Test successful user signup."""
    res = client.post(
        "/api/auth/signup",
        json={"username": "alice", "email": "alice@test.com", "password": "pass123"},
    )
    assert res.status_code == 201
    assert res.json["message"] == "User created successfully"


def test_login_invalid(client):
    """Test login with invalid credentials returns 401."""
    res = client.post(
        "/api/auth/login", json={"email": "notfound@test.com", "password": "wrong"}
    )
    assert res.status_code == 401


def test_login_and_me(client, logged_in_user):  # pylint: disable=unused-argument
    """Test successful login and /me endpoint returns user data."""
    res = client.post(
        "/api/auth/login", json={"email": "user@test.com", "password": "anything"}
    )
    assert res.status_code == 200
    assert res.json["user"]["email"] == "user@test.com"

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json["email"] == "user@test.com"
