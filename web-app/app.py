"""
Flask application factory for the receipt scanner web app.

This module initializes the Flask app, configures Flask-Login,
registers blueprints, and sets up error handlers.
"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager

from database import db
from auth_routes import auth_bp
from routes import receipt_bp
from models import User

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader."""
    doc = db.get_user_by_id(user_id)
    return User(doc) if doc else None


def create_app():
    """Application factory for the web app."""
    load_dotenv()

    application = Flask(__name__)
    application.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    application.config["TESTING"] = os.getenv("TESTING", "False") == "True"

    # Connect to MongoDB unless running under pytest (where monkeypatch replaces connect)
    if not application.config["TESTING"]:
        db.connect()

    # Setup Flask-Login
    login_manager.init_app(application)
    login_manager.login_view = "auth.login"

    # Register blueprints
    application.register_blueprint(auth_bp)
    application.register_blueprint(receipt_bp)

    # Error handlers
    @application.errorhandler(400)
    def bad_request(_e):
        return {"error": "Bad Request"}, 400

    @application.errorhandler(404)
    def not_found(_e):
        return {"error": "Not Found"}, 404

    @application.errorhandler(500)
    def server_error(_e):
        return {"error": "Internal Server Error"}, 500

    @application.route("/")
    def index():
        # later you'll pull stats from DB; for now just stub
        return render_template("index.html",
                            total_spend_month="$0.00",
                            total_receipts=0,
                            top_category=None,
                            recent_receipts=[])

    @application.route("/upload")
    def upload():
        return render_template("upload.html")

    @application.route("/history")
    def history():
        return render_template("history.html")

    @application.route("/analytics")
    def analytics():
        return render_template("analytics.html")

    return application


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)