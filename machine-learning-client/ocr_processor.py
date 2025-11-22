"""
OCR Processor Module for Receipt Scanning.

This module extracts text from receipt images using EasyOCR and parses
structured data using GPT-4o-mini API.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Tuple

import easyocr
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for lazy initialization
_ocr_reader: easyocr.Reader | None = None
_openai_client: OpenAI | None = None


def _get_ocr_reader() -> easyocr.Reader:
    """
    Get or initialize EasyOCR reader (lazy initialization).

    Returns:
        easyocr.Reader: Initialized EasyOCR reader instance.
    """
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("Initializing EasyOCR reader...")
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader


def _get_openai_client() -> OpenAI:
    """
    Get or initialize OpenAI client (lazy initialization).

    Returns:
        OpenAI: Initialized OpenAI client instance.

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set.
    """
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def extract_text(image: np.ndarray) -> List[Tuple[str, float]]:
    """
    Extract text from receipt image using EasyOCR.

    Args:
        image: NumPy array representing the receipt image.

    Returns:
        List of tuples containing (text, confidence) for each detected text.
        Returns empty list if OCR fails.

    Example:
        >>> import cv2
        >>> img = cv2.imread("receipt.jpg")
        >>> results = extract_text(img)
        >>> print(results[0][0])  # First detected text
    """
    try:
        reader = _get_ocr_reader()
        results = reader.readtext(image)
        # EasyOCR returns list of (bbox, text, confidence)
        # We return (text, confidence)
        return [(text, float(confidence)) for _, text, confidence in results]
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        return []


def parse_receipt(raw_text: str) -> Dict[str, Any]:
    """
    Parse receipt text using GPT-4o-mini to extract structured data.

    Args:
        raw_text: Raw OCR text string from receipt.

    Returns:
        Dictionary containing parsed receipt data with structure:
        {
            "merchant": str | None,
            "date": str | None,  # ISO format "YYYY-MM-DD"
            "total": float | None,
            "tax": float | None,
            "subtotal": float | None,
            "items": List[Dict[str, Any]],  # Each item: {"name": str, "quantity": int|float|None, "price": float, "unit_price": float|None}
            "category_hint": str | None,  # GPT's suggested expense category
            "raw_text": str,
            "confidence": float  # Average OCR confidence (not used here, set to 1.0)
        }

    Example:
        >>> text = "WALMART\\n01/15/2025\\nMilk $4.99\\nTOTAL $4.99"
        >>> result = parse_receipt(text)
        >>> print(result["merchant"])  # "WALMART"
    """
    if not raw_text or not raw_text.strip():
        logger.warning("Empty receipt text provided")
        return {
            "merchant": None,
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "items": [],
            "category_hint": None,
            "raw_text": raw_text,
            "confidence": 0.0,
        }

    # Truncate very long text to save tokens (keep first ~2000 chars)
    truncated_text = raw_text[:2000] if len(raw_text) > 2000 else raw_text

    try:
        client = _get_openai_client()

        system_prompt = (
            "You are a receipt parsing assistant. Extract structured data "
            "from receipt text. Return a JSON object with the following fields:\n"
            "- merchant (string or null): Store/merchant name\n"
            "- date (string or null): Date in ISO format YYYY-MM-DD only\n"
            "- total (number or null): Total amount as a float\n"
            "- tax (number or null): Tax amount as a float\n"
            "- subtotal (number or null): Subtotal amount as a float\n"
            "- items (array or null): Array of objects, each with: name (string), "
            "quantity (number or null), price (number), unit_price (number or null)\n"
            "- category_hint (string or null): Suggested expense category. "
            "MUST be exactly one of: Dining, Groceries, Transportation, "
            "Office Supplies, Travel & Lodging, Entertainment, Utilities, "
            "Healthcare, Shopping, Sports & Fitness, or Other. "
            "Use null only if category cannot be determined.\n\n"
            "IMPORTANT FORMAT REQUIREMENTS:\n"
            "- All dates MUST be in ISO format YYYY-MM-DD (e.g., '2025-01-15')\n"
            "- All numbers MUST be valid JSON numbers (floats, not strings)\n"
            "- category_hint MUST match one of the 11 categories exactly (case-sensitive)\n"
            "- Use null for any field that cannot be determined\n"
            "- Return valid JSON only, no additional text or formatting"
        )

        user_prompt = f"Extract receipt data from this text:\n\n{truncated_text}"

        # Retry logic with exponential backoff (max 3 retries)
        max_retries = 3
        retry_delay = 1  # Start with 1 second

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temperature for consistent parsing
                )
                break  # Success, exit retry loop
            except Exception as api_error:
                # Check if it's a rate limit error (429) or timeout
                error_str = str(api_error).lower()
                is_rate_limit = "429" in error_str or "rate limit" in error_str
                is_timeout = "timeout" in error_str

                if (is_rate_limit or is_timeout) and attempt < max_retries - 1:
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{max_retries}): "
                        f"{str(api_error)}. Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Not retryable or last attempt, re-raise
                    raise

        # Parse JSON response
        parsed_data = json.loads(response.choices[0].message.content)

        # Ensure all required fields exist with proper types
        result = {
            "merchant": parsed_data.get("merchant"),
            "date": parsed_data.get("date"),
            "total": (
                float(parsed_data["total"])
                if parsed_data.get("total") is not None
                else None
            ),
            "tax": (
                float(parsed_data["tax"])
                if parsed_data.get("tax") is not None
                else None
            ),
            "subtotal": (
                float(parsed_data["subtotal"])
                if parsed_data.get("subtotal") is not None
                else None
            ),
            "items": parsed_data.get("items", []),
            "category_hint": parsed_data.get("category_hint"),
            "raw_text": raw_text,
            "confidence": 1.0,  # LLM parsing doesn't have confidence score
        }

        # Validate and normalize items
        normalized_items = []
        for item in result["items"]:
            normalized_item = {
                "name": item.get("name", ""),
                "quantity": (
                    item.get("quantity") if item.get("quantity") is not None else None
                ),
                "price": (
                    float(item["price"]) if item.get("price") is not None else 0.0
                ),
                "unit_price": (
                    float(item["unit_price"])
                    if item.get("unit_price") is not None
                    else None
                ),
            }
            normalized_items.append(normalized_item)
        result["items"] = normalized_items

        return result

    except ValueError as e:
        # Missing API key
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        # API errors, network issues, etc.
        logger.error(f"LLM parsing failed: {str(e)}")
        # Return partial data with raw text
        return {
            "merchant": None,
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "items": [],
            "category_hint": None,
            "raw_text": raw_text,
            "confidence": 0.0,
        }


def process_receipt(image: np.ndarray) -> Dict[str, Any]:
    """
    Main entry point: Process receipt image to extract structured data.

    This function combines OCR extraction and LLM parsing to return
    a complete receipt data dictionary.

    Args:
        image: NumPy array representing the receipt image (from OpenCV).

    Returns:
        Dictionary containing parsed receipt data with structure:
        {
            "merchant": str | None,
            "date": str | None,  # ISO format "YYYY-MM-DD"
            "total": float | None,
            "tax": float | None,
            "subtotal": float | None,
            "items": List[Dict[str, Any]],
            "category_hint": str | None,  # GPT's suggested expense category
            "raw_text": str,
            "confidence": float  # Average OCR confidence
        }

    Raises:
        ValueError: If image is invalid or empty.

    Example:
        >>> import cv2
        >>> img = cv2.imread("receipt.jpg")
        >>> receipt_data = process_receipt(img)
        >>> print(receipt_data["merchant"])
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image: image is None or empty")

    # Extract text using OCR
    ocr_results = extract_text(image)

    if not ocr_results:
        logger.warning("No text extracted from image")
        return {
            "merchant": None,
            "date": None,
            "total": None,
            "tax": None,
            "subtotal": None,
            "items": [],
            "category_hint": None,
            "raw_text": "",
            "confidence": 0.0,
        }

    # Combine OCR text into single string
    raw_text = "\n".join([text for text, _ in ocr_results])

    # Calculate average confidence
    if ocr_results:
        avg_confidence = sum(conf for _, conf in ocr_results) / len(ocr_results)
    else:
        avg_confidence = 0.0

    # Parse receipt using LLM
    parsed_data = parse_receipt(raw_text)

    # Update confidence from OCR
    parsed_data["confidence"] = avg_confidence

    return parsed_data
