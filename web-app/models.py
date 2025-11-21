"""
This class adapts MongoDB user documents into objects
compatible with Flask-Login session management.
"""

from flask_login import UserMixin


class User(UserMixin):
    """Wrapper class so Flask-Login can manage user sessions."""

    def __init__(self, document):
        # Flask-Login requires an attribute named "id"
        self.id = str(document["_id"])
        self.username = document.get("username")
        self.email = document.get("email")
        self.preferences = document.get("preferences", {})

    def to_json(self):
        """Return a JSON-safe representation for frontend consumption."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "preferences": self.preferences,
        }