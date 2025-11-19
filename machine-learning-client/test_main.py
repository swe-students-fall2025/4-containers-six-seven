"""
Integration tests for main.py module.

Tests the complete pipeline with mocked OCR, classifier, and database components.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

# Mock dependencies before importing main
sys.modules['cv2'] = MagicMock()
sys.modules['easyocr'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Import numpy for tests (should be available)
import numpy as np

from main import (
    process_single_receipt,
    process_batch,
    show_statistics,
    main,
)


class TestProcessSingleReceipt:
    """Test suite for process_single_receipt function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mocked database instance."""
        db = MagicMock()
        db.insert_receipt.return_value = "test_receipt_id_123"
        return db

    @pytest.fixture
    def mock_image(self):
        """Create a dummy image array."""
        return np.zeros((100, 100, 3), dtype=np.uint8)

    def test_process_single_receipt_success(self, mock_db, mock_image):
        """Test successful processing of a single receipt."""
        with patch("main.os.path.exists", return_value=True), \
             patch("main.cv2.imread", return_value=mock_image), \
             patch("main.process_receipt") as mock_ocr, \
             patch("main.add_category_to_receipt") as mock_classify:

            # Mock OCR result
            mock_ocr.return_value = {
                "merchant": "Starbucks",
                "date": "2025-11-18",
                "total": 12.50,
                "items": [{"name": "Coffee", "price": 12.50}],
            }

            # Mock classification result
            mock_classify.return_value = {
                "merchant": "Starbucks",
                "date": "2025-11-18",
                "total": 12.50,
                "items": [{"name": "Coffee", "price": 12.50}],
                "category": "Food & Dining",
            }

            # Process receipt
            result = process_single_receipt("test_receipt.jpg", mock_db)

            # Verify OCR was called
            mock_ocr.assert_called_once_with(mock_image)

            # Verify classification was called
            mock_classify.assert_called_once()

            # Verify database insert was called
            mock_db.insert_receipt.assert_called_once()

            # Verify result
            assert result["merchant"] == "Starbucks"
            assert result["category"] == "Food & Dining"
            assert result["_id"] == "test_receipt_id_123"

    def test_process_single_receipt_file_not_found(self, mock_db):
        """Test handling of non-existent file."""
        with patch("main.os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                process_single_receipt("nonexistent.jpg", mock_db)

            assert "not found" in str(exc_info.value).lower()

    def test_process_single_receipt_invalid_image(self, mock_db):
        """Test handling of invalid image file."""
        with patch("main.os.path.exists", return_value=True), \
             patch("main.cv2.imread", return_value=None):

            with pytest.raises(ValueError) as exc_info:
                process_single_receipt("invalid.jpg", mock_db)

            assert "could not load" in str(exc_info.value).lower()

    def test_process_single_receipt_db_insert_fails(self, mock_db, mock_image):
        """Test handling when database insert fails."""
        mock_db.insert_receipt.return_value = None

        with patch("main.os.path.exists", return_value=True), \
             patch("main.cv2.imread", return_value=mock_image), \
             patch("main.process_receipt") as mock_ocr, \
             patch("main.add_category_to_receipt") as mock_classify:

            mock_ocr.return_value = {"merchant": "Test", "total": 10.00}
            mock_classify.return_value = {"merchant": "Test", "total": 10.00, "category": "Other"}

            result = process_single_receipt("test.jpg", mock_db)

            # Should still return result even if insert fails
            assert "_id" not in result or result["_id"] is None


class TestProcessBatch:
    """Test suite for process_batch function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mocked database instance."""
        return MagicMock()

    def test_process_batch_success(self, mock_db, tmp_path):
        """Test successful batch processing."""
        # Create temporary test images
        img1 = tmp_path / "receipt1.jpg"
        img2 = tmp_path / "receipt2.png"
        img1.touch()
        img2.touch()

        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("main.cv2.imread", return_value=mock_image), \
             patch("main.process_receipt") as mock_ocr, \
             patch("main.add_category_to_receipt") as mock_classify:

            mock_ocr.return_value = {"merchant": "Test", "total": 10.00}
            mock_classify.return_value = {"merchant": "Test", "total": 10.00, "category": "Other"}
            mock_db.insert_receipt.return_value = "test_id"

            results = process_batch(str(tmp_path), mock_db)

            assert results["total"] == 2
            assert results["processed"] == 2
            assert results["failed"] == 0

    def test_process_batch_directory_not_found(self, mock_db):
        """Test handling of non-existent directory."""
        with pytest.raises(NotADirectoryError):
            process_batch("/nonexistent/directory", mock_db)

    def test_process_batch_no_images(self, mock_db, tmp_path):
        """Test handling of directory with no images."""
        results = process_batch(str(tmp_path), mock_db)

        assert results["total"] == 0
        assert results["processed"] == 0
        assert results["failed"] == 0

    def test_process_batch_partial_failure(self, mock_db, tmp_path):
        """Test batch processing with some failures."""
        # Create test images
        img1 = tmp_path / "good.jpg"
        img2 = tmp_path / "bad.jpg"
        img1.touch()
        img2.touch()

        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)

        def mock_imread_side_effect(path):
            if "bad" in str(path):
                return None  # Simulate failed image load
            return mock_image

        with patch("main.cv2.imread", side_effect=mock_imread_side_effect), \
             patch("main.process_receipt") as mock_ocr, \
             patch("main.add_category_to_receipt") as mock_classify:

            mock_ocr.return_value = {"merchant": "Test", "total": 10.00}
            mock_classify.return_value = {"merchant": "Test", "total": 10.00, "category": "Other"}
            mock_db.insert_receipt.return_value = "test_id"

            results = process_batch(str(tmp_path), mock_db)

            assert results["total"] == 2
            assert results["processed"] == 1
            assert results["failed"] == 1


class TestShowStatistics:
    """Test suite for show_statistics function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mocked database instance."""
        db = MagicMock()
        db.get_statistics.return_value = {
            "total_receipts": 10,
            "total_amount": 250.50,
            "by_category": [
                {"_id": "Food & Dining", "count": 5, "total": 100.00},
                {"_id": "Shopping", "count": 3, "total": 120.50},
                {"_id": "Transportation", "count": 2, "total": 30.00},
            ],
        }
        return db

    def test_show_statistics(self, mock_db, capsys):
        """Test displaying database statistics."""
        show_statistics(mock_db)

        captured = capsys.readouterr()
        output = captured.out

        # Verify key information is displayed
        assert "Total Receipts: 10" in output
        assert "Total Amount: $250.50" in output
        assert "Food & Dining" in output
        assert "Shopping" in output
        assert "Transportation" in output

    def test_show_statistics_empty_db(self, capsys):
        """Test displaying statistics for empty database."""
        mock_db = MagicMock()
        mock_db.get_statistics.return_value = {
            "total_receipts": 0,
            "total_amount": 0.0,
            "by_category": [],
        }

        show_statistics(mock_db)

        captured = capsys.readouterr()
        output = captured.out

        assert "Total Receipts: 0" in output
        assert "Total Amount: $0.00" in output


class TestMainCLI:
    """Test suite for main CLI function."""

    def test_main_no_arguments(self, capsys):
        """Test main with no arguments shows help."""
        with patch("sys.argv", ["main.py"]), \
             pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Must specify" in captured.out or "usage:" in captured.out.lower()

    def test_main_with_image_argument(self):
        """Test main with --image argument."""
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("sys.argv", ["main.py", "--image", "test.jpg"]), \
             patch("main.ReceiptDatabase") as MockDB, \
             patch("main.os.path.exists", return_value=True), \
             patch("main.cv2.imread", return_value=mock_image), \
             patch("main.process_receipt") as mock_ocr, \
             patch("main.add_category_to_receipt") as mock_classify:

            # Setup mocks
            mock_db_instance = MagicMock()
            mock_db_instance.connect.return_value = True
            mock_db_instance.insert_receipt.return_value = "test_id"
            MockDB.return_value = mock_db_instance

            mock_ocr.return_value = {"merchant": "Starbucks", "total": 12.50}
            mock_classify.return_value = {
                "merchant": "Starbucks",
                "total": 12.50,
                "category": "Food & Dining",
            }

            main()

            # Verify database was initialized and connected
            MockDB.assert_called_once()
            mock_db_instance.connect.assert_called_once()
            mock_db_instance.disconnect.assert_called_once()

    def test_main_with_stats_argument(self):
        """Test main with --stats argument."""
        with patch("sys.argv", ["main.py", "--stats"]), \
             patch("main.ReceiptDatabase") as MockDB, \
             patch("main.show_statistics") as mock_show_stats:

            # Setup mock
            mock_db_instance = MagicMock()
            mock_db_instance.connect.return_value = True
            MockDB.return_value = mock_db_instance

            main()

            # Verify show_statistics was called
            mock_show_stats.assert_called_once_with(mock_db_instance)
            mock_db_instance.disconnect.assert_called_once()

    def test_main_db_connection_failure(self, capsys):
        """Test main when database connection fails."""
        with patch("sys.argv", ["main.py", "--stats"]), \
             patch("main.ReceiptDatabase") as MockDB, \
             pytest.raises(SystemExit) as exc_info:

            mock_db_instance = MagicMock()
            mock_db_instance.connect.return_value = False
            MockDB.return_value = mock_db_instance

            main()

        assert exc_info.value.code == 1

    def test_main_keyboard_interrupt(self):
        """Test main handles keyboard interrupt gracefully."""
        with patch("sys.argv", ["main.py", "--stats"]), \
             patch("main.ReceiptDatabase") as MockDB, \
             pytest.raises(SystemExit) as exc_info:

            mock_db_instance = MagicMock()
            mock_db_instance.connect.return_value = True
            mock_db_instance.get_statistics.side_effect = KeyboardInterrupt()
            MockDB.return_value = mock_db_instance

            main()

        assert exc_info.value.code == 130  # Standard exit code for SIGINT

