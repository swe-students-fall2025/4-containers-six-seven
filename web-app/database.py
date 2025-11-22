"""
MongoDB database module for the web application.

This database layer handles:
- Users (signup, login)
- Receipts (CRUD, job queue insert, analytics fields)
- Secure password hashing
- ObjectId conversion
"""

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId
from werkzeug.security import generate_password_hash, check_password_hash


class WebAppDatabase:
    """MongoDB interface used by the web backend."""

    def __init__(
        self, mongo_uri: Optional[str] = None, mongo_db_name: Optional[str] = None
    ):
        # Construct MONGO_URI from components if not provided
        if mongo_uri:
            self.mongo_uri = mongo_uri
        elif os.getenv("MONGO_URI"):
            self.mongo_uri = os.getenv("MONGO_URI")
        else:
            # Build URI from MONGO_USER, MONGO_PASS, and host
            mongo_user = os.getenv("MONGO_USER", "admin")
            mongo_pass = os.getenv("MONGO_PASS", "password")
            # Default to localhost for local development, mongodb for Docker
            mongo_host = os.getenv("MONGO_HOST", "localhost")
            self.mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/"
            print(f"[DEBUG] MongoDB connection string: mongodb://{mongo_user}:***@{mongo_host}:27017/")
            print(f"[DEBUG] MONGO_HOST from env: {os.getenv('MONGO_HOST', 'NOT SET')}")
        self.mongo_db_name = mongo_db_name or os.getenv("MONGO_DB_NAME", "receipts_db")

        self.client = None
        self.db = None
        self.users = None
        self.receipts = None

    # CONNECTION
    def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")  # throws if server not reachable

            self.db = self.client[self.mongo_db_name]
            self.users = self.db["users"]
            self.receipts = self.db["receipts"]
            return True
        except ConnectionFailure as e:
            error_str = str(e)
            print(f"MongoDB connection failed: {e}")
            # Try connecting without authentication if auth fails
            if "Authentication failed" in error_str or "AuthenticationFailed" in error_str or "code: 18" in error_str:
                print("Authentication failed. Attempting connection without credentials...")
                return self._connect_without_auth()
            return False
        except Exception as e:
            error_str = str(e)
            print(f"MongoDB connection error: {e}")
            # Try connecting without authentication if it's an auth error
            if "Authentication failed" in error_str or "AuthenticationFailed" in error_str or "code: 18" in error_str:
                print("Authentication failed. Attempting connection without credentials...")
                return self._connect_without_auth()
            return False

    def _connect_without_auth(self) -> bool:
        """Attempt to connect to MongoDB without authentication (for local dev)."""
        try:
            mongo_host = os.getenv("MONGO_HOST", "localhost")
            # Try connection without username/password
            simple_uri = f"mongodb://{mongo_host}:27017/"
            self.client = MongoClient(simple_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            
            self.db = self.client[self.mongo_db_name]
            self.users = self.db["users"]
            self.receipts = self.db["receipts"]
            print("Connected to MongoDB without authentication.")
            return True
        except Exception as e:
            print(f"Failed to connect without authentication: {e}")
            return False

    def _ensure_connected(self):
        """Ensure database connection is established."""
        if self.users is None:
            if not self.connect():
                raise ConnectionFailure("Failed to connect to MongoDB. Please check your connection settings.")

    # USER METHODS
    def create_user(self, username: str, email: str, password: str) -> Optional[Dict]:
        """Create a new user with hashed password."""
        self._ensure_connected()
        if self.users.find_one({"email": email}):
            return None

        hashed_pw = generate_password_hash(password)
        doc = {
            "username": username,
            "email": email,
            "password_hash": hashed_pw,
            "preferences": {},
            "created_at": datetime.now(timezone.utc),
        }

        result = self.users.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Retrieve a user document by email address."""
        self._ensure_connected()
        return self.users.find_one({"email": email})

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by string ObjectId."""
        self._ensure_connected()
        doc = self.users.find_one({"_id": user_id}) or self.users.find_one(
            {"_id": ObjectId(user_id)}
        )
        return doc

    def verify_password(self, stored_hash: str, password: str) -> bool:
        """Check if the password matches the stored hash"""
        return check_password_hash(stored_hash, password)

    # RECEIPT METHODS
    def insert_receipt(self, user_id: str, image_path: str) -> str:
        """
        Insert a new pending receipt.
        ML worker will later:
            - read image_path
            - extract OCR
            - classify
            - update document
        """
        self._ensure_connected()
        doc = {
            "user_id": user_id,
            "image_path": image_path,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            # ML fields (to be filled by worker)
            "merchant": None,
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "items": [],
            "raw_text": None,
            "confidence": None,
            "category": None,
        }

        result = self.receipts.insert_one(doc)
        return str(result.inserted_id)

    def get_receipts_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all receipts for a given user, sorted by creation date."""
        self._ensure_connected()
        docs = list(
            self.receipts.find({"user_id": user_id}).sort("created_at", DESCENDING)
        )
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    def get_receipt_by_id(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single receipt by its ObjectID string"""
        self._ensure_connected()
        try:
            oid = ObjectId(receipt_id)
        except InvalidId:
            return None

        doc = self.receipts.find_one({"_id": oid})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def update_receipt(self, receipt_id: str, update_data: Dict[str, Any]) -> bool:
        """Manual editing of receipt fields."""
        self._ensure_connected()
        try:
            oid = ObjectId(receipt_id)
        except InvalidId:
            return False

        res = self.receipts.update_one({"_id": oid}, {"$set": update_data})
        return res.modified_count > 0

    def delete_receipt(self, receipt_id: str) -> bool:
        """Delete a receipt by its objectId string"""
        self._ensure_connected()
        try:
            oid = ObjectId(receipt_id)
        except InvalidId:
            return False

        res = self.receipts.delete_one({"_id": oid})
        return res.deleted_count > 0

    #
    # STATISTICS
    #
    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Minimal statistics for /api/receipts/statistics.
        The detailed analytics are computed in routes.py.
        """
        self._ensure_connected()
        total_count = self.receipts.count_documents({"user_id": user_id})
        return {"total_receipts": total_count}


# Global singleton used by the web app
db = WebAppDatabase()
