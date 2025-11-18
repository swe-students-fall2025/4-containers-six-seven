"""
Test script for testing OCR processor with real receipt images.

This script allows you to test the complete flow with actual API calls.
Make sure you have OPENAI_API_KEY set in your .env file.
"""

import cv2
import numpy as np
from ocr_processor import process_receipt


# Example: Test with a receipt image file
def test_receipt_from_file(image_path: str):
    """
    Test OCR processing with a receipt image file.

    Args:
        image_path: Path to the receipt image file (jpg, png, etc.)
    """
    print(f"Loading image from: {image_path}")

    # Load image using OpenCV
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return None

    print(f"Image loaded: {image.shape}")
    print("Processing receipt...")

    # Process the receipt
    result = process_receipt(image)

    # Print results
    print("\n" + "=" * 50)
    print("RECEIPT PROCESSING RESULTS")
    print("=" * 50)
    print(f"Merchant: {result.get('merchant', 'N/A')}")
    print(f"Date: {result.get('date', 'N/A')}")
    print(
        f"Total: ${result.get('total', 0):.2f}" if result.get("total") else "Total: N/A"
    )
    print(f"Tax: ${result.get('tax', 0):.2f}" if result.get("tax") else "Tax: N/A")
    print(
        f"Subtotal: ${result.get('subtotal', 0):.2f}"
        if result.get("subtotal")
        else "Subtotal: N/A"
    )
    print(f"OCR Confidence: {result.get('confidence', 0):.2%}")

    print(f"\nItems ({len(result.get('items', []))}):")
    for i, item in enumerate(result.get("items", []), 1):
        print(f"  {i}. {item.get('name', 'N/A')}")
        if item.get("quantity"):
            print(f"     Qty: {item.get('quantity')}")
        print(f"     Price: ${item.get('price', 0):.2f}")
        if item.get("unit_price"):
            print(f"     Unit Price: ${item.get('unit_price', 0):.2f}")

    print("\n" + "=" * 50)
    print("RAW OCR TEXT (first 500 chars):")
    print("=" * 50)
    raw_text = result.get("raw_text", "")
    print(raw_text[:500] + ("..." if len(raw_text) > 500 else ""))

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_real_receipt.py <path_to_receipt_image>")
        print("\nExample:")
        print("  python test_real_receipt.py test-data/receipt1.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    test_receipt_from_file(image_path)
