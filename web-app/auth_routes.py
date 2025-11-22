"""
Login/sign up/Logout page routes for the web application
"""
from flask import Blueprint, request, render_template
from flask_login import login_user, logout_user, login_required, current_user

from database import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/login")
def login_page():
    """Render the login page."""
    return render_template("login.html")


@auth_bp.get("/signup")
def signup_page():
    """Render the signup page."""
    return render_template("signup.html")


@auth_bp.post("/signup")
def signup():
    """
    Create a new user.

    Request JSON:
    {
        "username": "...",
        "email": "...",
        "password": "..."
    }
    """
    data = request.get_json() or {}

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return {"error": "Missing required fields"}, 400

    user_doc = db.create_user(username, email, password)
    if user_doc is None:
        return {"error": "Email already exists"}, 409

    return {"message": "User created successfully"}, 201


@auth_bp.post("/login")
def login():
    """
    Log a user in.

    Request JSON:
    {
        "email": "...",
        "password": "..."
    }
    """
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Missing fields"}, 400

    user_doc = db.get_user_by_email(email)
    if not user_doc:
        return {"error": "Invalid credentials"}, 401

    if not db.verify_password(user_doc["password_hash"], password):
        return {"error": "Invalid credentials"}, 401

    login_user(User(user_doc))
    return {"message": "Logged in", "user": User(user_doc).to_json()}, 200


@auth_bp.post("/logout")
@login_required
def logout():
    """End user session."""
    logout_user()
    return {"message": "Logged out"}, 200


@auth_bp.get("/me")
@login_required
def me():
    """Return the current logged-in user's profile."""
    return current_user.to_json()
