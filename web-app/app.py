import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from database import db
from auth_routes import auth_bp
from routes import receipt_bp

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader."""
    from models import User
    doc = db.get_user_by_id(user_id)
    return User(doc) if doc else None


def create_app():
    """Application factory for the web app."""
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["TESTING"] = os.getenv("TESTING", False)

    # Connect to MongoDB unless running under pytest (where monkeypatch replaces connect)
    if not app.config["TESTING"]:
        db.connect()

    # Setup Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(receipt_bp)

    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return {"error": "Bad Request"}, 400

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not Found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal Server Error"}, 500

    @app.route("/")
    def home():
        return {"status": "web-app running"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)