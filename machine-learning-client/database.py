"""
Database module for MongoDB operations.

This module handles all database interactions for the receipt scanner,
including CRUD operations and statistics queries.
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, PyMongoError


class ReceiptDatabase:
    """Handles MongoDB operations for receipt storage and retrieval."""

    def __init__(
        self,
        mongo_user: Optional[str] = None,
        mongo_pass: Optional[str] = None,
        mongo_db_name: Optional[str] = None,
        mongo_host: Optional[str] = None,
    ):
        """
        Initialize database connection.

        Args:
            mongo_user: MongoDB username (defaults to env var MONGO_USER)
            mongo_pass: MongoDB password (defaults to env var MONGO_PASS)
            mongo_db_name: Database name (defaults to env var MONGO_DB_NAME)
            mongo_host: MongoDB host (defaults to env var MONGO_HOST or 'localhost' for local dev)
        """
        self.mongo_user = mongo_user or os.getenv("MONGO_USER", "admin")
        self.mongo_pass = mongo_pass or os.getenv("MONGO_PASS", "password")
        self.mongo_db_name = mongo_db_name or os.getenv("MONGO_DB_NAME", "receipts_db")
        # Default to localhost for local development, mongodb for Docker
        self.mongo_host = mongo_host or os.getenv("MONGO_HOST", "localhost")

        self.client = None
        self.database = None
        self.collection = None

    def connect(self) -> bool:
        """
        Establish connection to MongoDB.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            connection_string = f"mongodb://{self.mongo_user}:{self.mongo_pass}@{self.mongo_host}:27017/"
            print(
                f"[DEBUG] Connecting to MongoDB at: mongodb://{self.mongo_user}:***@{self.mongo_host}:27017/"
            )
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command("ping")
            self.database = self.client[self.mongo_db_name]
            self.collection = self.database["receipts"]
            print("MongoDB connection successful")
            return True
        except ConnectionFailure as e:
            error_str = str(e)
            print(f"MongoDB connection failed: {e}")
            # Try connecting without authentication if auth fails
            if (
                "Authentication failed" in error_str
                or "AuthenticationFailed" in error_str
                or "code: 18" in error_str
            ):
                print(
                    "Authentication failed. Attempting connection without credentials..."
                )
                return self._connect_without_auth()
            return False
        except PyMongoError as e:
            error_str = str(e)
            print(f"MongoDB error: {e}")
            # Try connecting without authentication if it's an auth error
            if (
                "Authentication failed" in error_str
                or "AuthenticationFailed" in error_str
                or "code: 18" in error_str
            ):
                print(
                    "Authentication failed. Attempting connection without credentials..."
                )
                return self._connect_without_auth()
            return False

    def _connect_without_auth(self) -> bool:
        """Attempt to connect to MongoDB without authentication (for local dev)."""
        try:
            # Try connection without username/password
            simple_uri = f"mongodb://{self.mongo_host}:27017/"
            print(f"Trying connection without auth: {simple_uri}")
            self.client = MongoClient(simple_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")

            self.database = self.client[self.mongo_db_name]
            self.collection = self.database["receipts"]
            print("Connected to MongoDB without authentication.")
            return True
        except Exception as e:
            print(f"Failed to connect without authentication: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.client:
            self.client.close()

    def insert_receipt(self, receipt_data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a new receipt into the database.

        Args:
            receipt_data: Dictionary containing receipt information

        Returns:
            str: Receipt ID if successful, None otherwise
        """
        try:
            # Add timestamp if not present
            if "created_at" not in receipt_data:
                receipt_data["created_at"] = datetime.now(timezone.utc)

            result = self.collection.insert_one(receipt_data)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error inserting receipt: {e}")
            return None

    def get_receipt_by_id(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a receipt by its ID.

        Args:
            receipt_id: The receipt's unique identifier

        Returns:
            dict: Receipt data if found, None otherwise
        """
        try:
            from bson import ObjectId

            result = self.collection.find_one({"_id": ObjectId(receipt_id)})
            if result:
                result["_id"] = str(result["_id"])
            return result
        except PyMongoError as e:
            print(f"Error retrieving receipt: {e}")
            return None

    def get_all_receipts(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all receipts with pagination.

        Args:
            limit: Maximum number of receipts to return
            skip: Number of receipts to skip

        Returns:
            list: List of receipt dictionaries
        """
        try:
            receipts = list(
                self.collection.find()
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            for receipt in receipts:
                receipt["_id"] = str(receipt["_id"])
            return receipts
        except PyMongoError as e:
            print(f"Error retrieving receipts: {e}")
            return []

    def update_receipt(self, receipt_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing receipt.

        Args:
            receipt_id: The receipt's unique identifier
            update_data: Dictionary with fields to update

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            from bson import ObjectId

            result = self.collection.update_one(
                {"_id": ObjectId(receipt_id)}, {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Error updating receipt: {e}")
            return False

    def delete_receipt(self, receipt_id: str) -> bool:
        """
        Delete a receipt by its ID.

        Args:
            receipt_id: The receipt's unique identifier

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            from bson import ObjectId

            result = self.collection.delete_one({"_id": ObjectId(receipt_id)})
            return result.deleted_count > 0
        except PyMongoError as e:
            print(f"Error deleting receipt: {e}")
            return False

    def get_receipts_by_category(
        self, category: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve receipts filtered by category.

        Args:
            category: Expense category to filter by
            limit: Maximum number of receipts to return

        Returns:
            list: List of receipt dictionaries
        """
        try:
            receipts = list(
                self.collection.find({"category": category})
                .sort("created_at", DESCENDING)
                .limit(limit)
            )
            for receipt in receipts:
                receipt["_id"] = str(receipt["_id"])
            return receipts
        except PyMongoError as e:
            print(f"Error retrieving receipts by category: {e}")
            return []

    def get_pending_receipts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve receipts with pending status for processing.

        Args:
            limit: Maximum number of receipts to return

        Returns:
            list: List of pending receipt dictionaries
        """
        try:
            receipts = list(
                self.collection.find({"status": "pending"})
                .sort("created_at", DESCENDING)
                .limit(limit)
            )
            for receipt in receipts:
                receipt["_id"] = str(receipt["_id"])
            return receipts
        except PyMongoError as e:
            print(f"Error retrieving pending receipts: {e}")
            return []

    def update_receipt_status(
        self, receipt_id: str, status: str, update_data: Dict[str, Any]
    ) -> bool:
        """
        Update receipt status and other fields after processing.

        Args:
            receipt_id: The receipt's unique identifier
            status: New status (e.g., "completed", "failed")
            update_data: Dictionary with fields to update (merchant, total, category, etc.)

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            from bson import ObjectId

            # Include status in update data
            update_data["status"] = status

            result = self.collection.update_one(
                {"_id": ObjectId(receipt_id)}, {"$set": update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Error updating receipt status: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate database statistics.

        Returns:
            dict: Statistics including total count, total amount, category breakdown
        """
        try:
            total_count = self.collection.count_documents({})

            # Calculate total amount spent
            pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}]
            total_result = list(self.collection.aggregate(pipeline))
            total_amount = total_result[0]["total"] if total_result else 0

            # Calculate category breakdown
            category_pipeline = [
                {
                    "$group": {
                        "_id": "$category",
                        "count": {"$sum": 1},
                        "total": {"$sum": "$total_amount"},
                    }
                }
            ]
            category_breakdown = list(self.collection.aggregate(category_pipeline))

            return {
                "total_receipts": total_count,
                "total_amount": round(total_amount, 2),
                "by_category": category_breakdown,
            }
        except PyMongoError as e:
            print(f"Error calculating statistics: {e}")
            return {
                "total_receipts": 0,
                "total_amount": 0,
                "by_category": [],
            }
