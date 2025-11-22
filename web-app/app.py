"""
Flask application factory for the receipt scanner web app.

This module initializes the Flask app, configures Flask-Login,
registers blueprints, and sets up error handlers.
"""

import os

from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager, current_user

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
        """Home page with statistics."""
        # Initialize default values
        total_spend_month = "$0.00"
        total_receipts = 0
        top_category = None
        recent_receipts = []

        # Fetch real stats if user is logged in
        if current_user.is_authenticated:
            receipts = db.get_receipts_by_user(current_user.id)
            total_receipts = len(receipts)

            # Calculate current month spending
            current_month = datetime.now().strftime("%Y-%m")
            month_total = sum(
                r.get("total", 0) or 0
                for r in receipts
                if r.get("date") and r.get("date", "")[:7] == current_month
            )
            total_spend_month = f"${month_total:.2f}"

            # Find top category
            category_totals = {}
            for r in receipts:
                category = r.get("category") or "Uncategorized"
                total = r.get("total") or 0
                category_totals[category] = category_totals.get(category, 0) + total

            if category_totals:
                top_category = max(category_totals.items(), key=lambda x: x[1])[0]

            # Get recent receipts (limit 5, sorted by date)
            completed_receipts = [
                r for r in receipts if r.get("status") == "completed" and r.get("date")
            ]
            completed_receipts.sort(key=lambda x: x.get("date", ""), reverse=True)
            recent_receipts = completed_receipts[:5]

        return render_template(
            "index.html",
            total_spend_month=total_spend_month,
            total_receipts=total_receipts,
            top_category=top_category,
            recent_receipts=recent_receipts,
        )

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
