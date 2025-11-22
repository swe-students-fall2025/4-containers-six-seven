"""
Unit tests for database.py module.

Tests all CRUD operations and statistics functions using mocked MongoDB.
"""

import pytest
import datetime
from unittest.mock import MagicMock, patch
from database import ReceiptDatabase

# Unique test data using timestamp
random_time = datetime.datetime.now().time()
test_merchant = f"Test Store {random_time}"
test_amount = 99.99


class TestDatabase:
    """Test suite for the database module."""

    @pytest.fixture
    def db(self):
        """
        Create and yield a database instance with mocked MongoDB connection.
        This fixture sets up a mocked database before each test and cleans up after.
        """
        with patch("database.MongoClient") as mock_client:
            # Mock the MongoDB client
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # Mock successful connection ping
            mock_instance.admin.command.return_value = {"ok": 1}

            # Mock database and collection
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_instance.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection

            # Create database instance
            database = ReceiptDatabase(
                mongo_user="test_user", mongo_pass="test_pass", mongo_db_name="test_db"
            )
            database.connect()

            yield database

            # Cleanup
            database.disconnect()

    def test_sanity_check(self, db):
        """
        Test debugging - making sure that we can run a simple test that always passes.
        """
        expected = True
        actual = True
        assert actual == expected, "Expected True to be equal to True!"

    def test_connection(self, db):
        """Test database connection is established"""
        assert db.client is not None, "Database client should be connected"
        assert db.database is not None, "Database should be accessible"
        assert db.collection is not None, "Collection should be accessible"

    def test_insert_receipt(self, db):
        """Test inserting a receipt into the database"""
        # Mock successful insert
        mock_result = MagicMock()
        mock_result.inserted_id = "507f1f77bcf86cd799439011"
        db.collection.insert_one.return_value = mock_result

        receipt_data = {
            "merchant": test_merchant,
            "total_amount": test_amount,
            "date": "2025-11-18",
            "category": "Shopping",
        }

        receipt_id = db.insert_receipt(receipt_data)

        assert receipt_id == "507f1f77bcf86cd799439011", "Should return inserted ID"
        assert "created_at" in receipt_data, "Should add created_at timestamp"

    @patch("bson.ObjectId")
    def test_get_receipt_by_id(self, mock_object_id, db):
        """Test retrieving a receipt by its ID"""
        mock_object_id.return_value = "507f1f77bcf86cd799439011"

        db.collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "merchant": test_merchant,
            "total_amount": test_amount,
            "category": "Shopping",
        }

        receipt = db.get_receipt_by_id("507f1f77bcf86cd799439011")

        assert receipt is not None, "Should find the receipt"
        assert receipt["merchant"] == test_merchant, "Merchant should match"
        assert receipt["total_amount"] == test_amount, "Amount should match"

    def test_get_all_receipts(self, db):
        """Test retrieving all receipts with pagination"""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"_id": "id1", "merchant": "Store1", "total_amount": 10.00},
            {"_id": "id2", "merchant": "Store2", "total_amount": 20.00},
        ]
        db.collection.find.return_value = mock_cursor

        receipts = db.get_all_receipts(limit=10, skip=0)

        assert len(receipts) == 2, "Should return 2 receipts"
        assert receipts[0]["merchant"] == "Store1", "First receipt should be Store1"
        assert receipts[1]["merchant"] == "Store2", "Second receipt should be Store2"

    @patch("bson.ObjectId")
    def test_update_receipt(self, mock_object_id, db):
        """Test updating an existing receipt"""
        mock_object_id.return_value = "507f1f77bcf86cd799439011"

        mock_result = MagicMock()
        mock_result.modified_count = 1
        db.collection.update_one.return_value = mock_result

        update_data = {"category": "Food & Dining"}
        result = db.update_receipt("507f1f77bcf86cd799439011", update_data)

        assert result is True, "Update should succeed"

    @patch("bson.ObjectId")
    def test_delete_receipt(self, mock_object_id, db):
        """Test deleting a receipt"""
        mock_object_id.return_value = "507f1f77bcf86cd799439011"

        mock_result = MagicMock()
        mock_result.deleted_count = 1
        db.collection.delete_one.return_value = mock_result

        result = db.delete_receipt("507f1f77bcf86cd799439011")

        assert result is True, "Delete should succeed"

    def test_get_receipts_by_category(self, db):
        """Test retrieving receipts filtered by category"""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"_id": "id1", "merchant": "McDonald's", "category": "Food & Dining"},
            {"_id": "id2", "merchant": "Starbucks", "category": "Food & Dining"},
        ]
        db.collection.find.return_value = mock_cursor

        receipts = db.get_receipts_by_category("Food & Dining", limit=10)

        assert len(receipts) == 2, "Should return 2 receipts"
        assert all(
            r["category"] == "Food & Dining" for r in receipts
        ), "All should be Food & Dining"

    def test_get_statistics(self, db):
        """Test calculating database statistics"""
        db.collection.count_documents.return_value = 5
        db.collection.aggregate.side_effect = [
            [{"_id": None, "total": 150.50}],
            [
                {"_id": "Food & Dining", "count": 3, "total": 100.00},
                {"_id": "Shopping", "count": 2, "total": 50.50},
            ],
        ]

        stats = db.get_statistics()

        assert stats["total_receipts"] == 5, "Should have 5 total receipts"
        assert stats["total_amount"] == 150.50, "Total amount should be 150.50"
        assert len(stats["by_category"]) == 2, "Should have 2 categories"
