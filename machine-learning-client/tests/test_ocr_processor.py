"""
Unit tests for ocr_processor module.

Tests cover OCR extraction, LLM parsing, and end-to-end processing
with mocked dependencies to avoid API calls and model downloads.
"""

import json
import os
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from ocr_processor import (
    _get_openai_client,
    _get_ocr_reader,
    extract_text,
    parse_receipt,
    process_receipt,
)


class TestExtractText:
    """Tests for extract_text function."""

    @patch("ocr_processor._get_ocr_reader")
    def test_extract_text_success(self, mock_get_reader):
        """Test successful text extraction."""
        # Mock OCR reader
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            ([[0, 0], [10, 0], [10, 10], [0, 10]], "WALMART", 0.95),
            ([[0, 20], [10, 20], [10, 30], [0, 30]], "01/15/2025", 0.90),
            ([[0, 40], [10, 40], [10, 50], [0, 50]], "Milk $4.99", 0.85),
        ]
        mock_get_reader.return_value = mock_reader

        # Create dummy image
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Test extraction
        results = extract_text(image)

        # Verify results
        assert len(results) == 3
        assert results[0][0] == "WALMART"
        assert results[0][1] == 0.95
        assert results[1][0] == "01/15/2025"
        assert results[2][0] == "Milk $4.99"

    @patch("ocr_processor._get_ocr_reader")
    def test_extract_text_empty_image(self, mock_get_reader):
        """Test extraction with empty image."""
        mock_reader = MagicMock()
        mock_reader.readtext.return_value = []
        mock_get_reader.return_value = mock_reader

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        results = extract_text(image)

        assert results == []

    @patch("ocr_processor._get_ocr_reader")
    def test_extract_text_ocr_failure(self, mock_get_reader):
        """Test handling of OCR failure."""
        mock_reader = MagicMock()
        mock_reader.readtext.side_effect = Exception("OCR error")
        mock_get_reader.return_value = mock_reader

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        results = extract_text(image)

        assert results == []


class TestParseReceipt:
    """Tests for parse_receipt function."""

    @patch("ocr_processor._get_openai_client")
    def test_parse_receipt_success(self, mock_get_client):
        """Test successful receipt parsing."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "merchant": "WALMART",
                            "date": "2025-01-15",
                            "total": 45.67,
                            "tax": 3.65,
                            "subtotal": 42.02,
                            "items": [
                                {
                                    "name": "Milk 2%",
                                    "quantity": 2,
                                    "price": 9.98,
                                    "unit_price": 4.99,
                                },
                                {
                                    "name": "Whole Wheat Bread",
                                    "quantity": 1,
                                    "price": 2.49,
                                    "unit_price": None,
                                },
                            ],
                        }
                    )
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        raw_text = "WALMART\n01/15/2025\nMilk 2% $9.98\nBread $2.49\nTOTAL $45.67"

        result = parse_receipt(raw_text)

        assert result["merchant"] == "WALMART"
        assert result["date"] == "2025-01-15"
        assert result["total"] == 45.67
        assert result["tax"] == 3.65
        assert result["subtotal"] == 42.02
        assert len(result["items"]) == 2
        assert result["items"][0]["name"] == "Milk 2%"
        assert result["items"][0]["quantity"] == 2
        assert result["items"][0]["price"] == 9.98
        assert result["raw_text"] == raw_text

    @patch("ocr_processor._get_openai_client")
    def test_parse_receipt_partial_data(self, mock_get_client):
        """Test parsing with partial data (some fields missing)."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "merchant": "STORE",
                            "date": None,
                            "total": 10.50,
                            "tax": None,
                            "subtotal": None,
                            "items": [],
                        }
                    )
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        raw_text = "STORE\nItem $10.50"

        result = parse_receipt(raw_text)

        assert result["merchant"] == "STORE"
        assert result["date"] is None
        assert result["total"] == 10.50
        assert result["tax"] is None
        assert result["items"] == []

    def test_parse_receipt_empty_text(self):
        """Test parsing with empty text."""
        result = parse_receipt("")

        assert result["merchant"] is None
        assert result["date"] is None
        assert result["total"] is None
        assert result["items"] == []
        assert result["raw_text"] == ""
        assert result["confidence"] == 0.0

    def test_parse_receipt_whitespace_only(self):
        """Test parsing with whitespace-only text."""
        result = parse_receipt("   \n\t  ")

        assert result["merchant"] is None
        assert result["items"] == []

    @patch("ocr_processor._get_openai_client")
    def test_parse_receipt_api_error(self, mock_get_client):
        """Test handling of API errors."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        raw_text = "Some receipt text"

        result = parse_receipt(raw_text)

        # Should return partial data with raw text
        assert result["merchant"] is None
        assert result["raw_text"] == raw_text
        assert result["confidence"] == 0.0

    @patch("ocr_processor.time.sleep")
    @patch("ocr_processor._get_openai_client")
    def test_parse_receipt_retry_on_rate_limit(self, mock_get_client, mock_sleep):
        """Test retry logic on rate limit errors."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "merchant": "STORE",
                            "date": "2025-01-15",
                            "total": 10.0,
                            "tax": None,
                            "subtotal": None,
                            "items": [],
                        }
                    )
                )
            )
        ]

        mock_client = MagicMock()
        # First call fails with rate limit, second succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("429 rate limit exceeded"),
            mock_response,
        ]
        mock_get_client.return_value = mock_client

        raw_text = "STORE\n01/15/2025\nItem $10.00"

        result = parse_receipt(raw_text)

        # Should succeed after retry
        assert result["merchant"] == "STORE"
        assert mock_sleep.called  # Verify retry delay was called
        assert mock_client.chat.completions.create.call_count == 2

    @patch("ocr_processor._get_openai_client")
    def test_parse_receipt_long_text_truncation(self, mock_get_client):
        """Test that very long text is truncated."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "merchant": "STORE",
                            "date": "2025-01-15",
                            "total": 10.0,
                            "tax": None,
                            "subtotal": None,
                            "items": [],
                        }
                    )
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Create text longer than 2000 chars
        long_text = "A" * 2500

        result = parse_receipt(long_text)

        # Verify truncation happened (check call argument)
        call_args = mock_client.chat.completions.create.call_args
        user_message = call_args[1]["messages"][1]["content"]
        assert len(user_message.split("\n\n")[1]) <= 2000

        assert result["merchant"] == "STORE"

    def test_parse_receipt_missing_api_key(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("ocr_processor._openai_client", None):
                with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                    parse_receipt("test text")


class TestProcessReceipt:
    """Tests for process_receipt function."""

    @patch("ocr_processor.parse_receipt")
    @patch("ocr_processor.extract_text")
    def test_process_receipt_success(self, mock_extract, mock_parse):
        """Test successful end-to-end processing."""
        # Mock OCR extraction
        mock_extract.return_value = [
            ("WALMART", 0.95),
            ("01/15/2025", 0.90),
            ("Milk $4.99", 0.85),
        ]

        # Mock parsing
        mock_parse.return_value = {
            "merchant": "WALMART",
            "date": "2025-01-15",
            "total": 4.99,
            "tax": None,
            "subtotal": None,
            "items": [
                {"name": "Milk", "quantity": None, "price": 4.99, "unit_price": None}
            ],
            "raw_text": "WALMART\n01/15/2025\nMilk $4.99",
            "confidence": 1.0,
        }

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = process_receipt(image)

        assert result["merchant"] == "WALMART"
        assert result["date"] == "2025-01-15"
        assert result["total"] == 4.99
        # Confidence should be from OCR, not LLM
        assert result["confidence"] == pytest.approx(0.90, abs=0.01)

    @patch("ocr_processor.extract_text")
    def test_process_receipt_no_text_extracted(self, mock_extract):
        """Test processing when no text is extracted."""
        mock_extract.return_value = []

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = process_receipt(image)

        assert result["merchant"] is None
        assert result["raw_text"] == ""
        assert result["confidence"] == 0.0

    def test_process_receipt_invalid_image_none(self):
        """Test processing with None image."""
        with pytest.raises(ValueError, match="Invalid image"):
            process_receipt(None)

    def test_process_receipt_invalid_image_empty(self):
        """Test processing with empty image."""
        empty_image = np.array([])
        with pytest.raises(ValueError, match="Invalid image"):
            process_receipt(empty_image)

    @patch("ocr_processor.parse_receipt")
    @patch("ocr_processor.extract_text")
    def test_process_receipt_confidence_calculation(self, mock_extract, mock_parse):
        """Test that confidence is calculated correctly from OCR."""
        # Mock OCR with varying confidence scores
        mock_extract.return_value = [
            ("Text1", 0.9),
            ("Text2", 0.8),
            ("Text3", 0.7),
        ]

        mock_parse.return_value = {
            "merchant": "STORE",
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "items": [],
            "raw_text": "Text1\nText2\nText3",
            "confidence": 1.0,  # This will be overwritten
        }

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = process_receipt(image)

        # Average of 0.9, 0.8, 0.7 = 0.8
        assert result["confidence"] == pytest.approx(0.8, abs=0.01)


class TestLazyInitialization:
    """Tests for lazy initialization of OCR reader and OpenAI client."""

    @patch("easyocr.Reader")
    def test_ocr_reader_lazy_init(self, mock_reader_class):
        """Test that OCR reader is initialized only once."""
        # Reset global
        import ocr_processor

        ocr_processor._ocr_reader = None

        # First call should initialize
        reader1 = _get_ocr_reader()
        assert mock_reader_class.call_count == 1

        # Second call should reuse
        reader2 = _get_ocr_reader()
        assert mock_reader_class.call_count == 1
        assert reader1 is reader2

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_openai_client_lazy_init(self):
        """Test that OpenAI client is initialized only once."""
        import ocr_processor

        ocr_processor._openai_client = None

        # First call should initialize
        client1 = _get_openai_client()
        assert client1 is not None

        # Second call should reuse
        client2 = _get_openai_client()
        assert client1 is client2

    @patch.dict(os.environ, {}, clear=True)
    def test_openai_client_missing_key(self):
        """Test error when API key is missing."""
        import ocr_processor

        ocr_processor._openai_client = None

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            _get_openai_client()
