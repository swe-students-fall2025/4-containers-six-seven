"""
Worker script for processing pending receipts.

This script runs as a long-running process that polls the database
for receipts with status "pending", processes them through OCR and
classification, and updates them with the results.
"""

import logging
import os
import time
from typing import Dict, Any

import cv2
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv()

from ocr_processor import process_receipt
from expense_classifier import add_category_to_receipt
from database import ReceiptDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Polling interval in seconds
POLL_INTERVAL = 5


def process_pending_receipt(receipt: Dict[str, Any], db: ReceiptDatabase) -> bool:
    """
    Process a single pending receipt.

    Args:
        receipt: Receipt document from database
        db: Database instance for updating receipt

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    receipt_id = receipt.get("_id")
    image_path = receipt.get("image_path")

    if not receipt_id or not image_path:
        logger.error(f"Invalid receipt document: missing _id or image_path")
        return False

    logger.info(f"Processing receipt {receipt_id} from {image_path}")

    try:
        # Normalize the path first
        original_path = image_path
        image_path = os.path.normpath(image_path)
        filename = os.path.basename(image_path)

        logger.info(f"Processing receipt with image path: {original_path}")

        # In Docker, files are in /app/uploads (shared volume)
        # The path stored in DB might be /uploads/filename or /app/uploads/filename
        # Try both Docker volume location and original path
        docker_volume_path = os.path.join("/app", "uploads", filename)

        # List of paths to try (Docker first, then original, then local dev paths)
        paths_to_try = [
            docker_volume_path,  # Docker volume location (most likely in Docker)
            image_path,  # Original path as stored (works for both Docker and local)
        ]

        # Add local dev paths if we're not in Docker (path doesn't start with /app)
        # This ensures local development still works
        if not image_path.startswith("/app"):
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )
            # Add local dev paths as fallbacks (won't interfere if original path works)
            paths_to_try.extend(
                [
                    os.path.join(project_root, "uploads", filename),
                    os.path.join(project_root, "web-app", "uploads", filename),
                    os.path.join(project_root, image_path.lstrip("/")),
                ]
            )

        # Try each path
        found_path = None
        for path_to_try in paths_to_try:
            path_to_try = os.path.normpath(path_to_try)
            logger.info(f"Checking path: {path_to_try}")
            if os.path.exists(path_to_try):
                found_path = path_to_try
                logger.info(f"Found file at: {found_path}")
                break

        if not found_path:
            logger.error(
                f"Image file not found. Original: {original_path}, Tried: {paths_to_try}"
            )
            # Update status to failed
            db.update_receipt_status(
                receipt_id,
                "failed",
                {"error": f"Image file not found: {original_path}"},
            )
            return False

        image_path = found_path

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not load image: {image_path}")
            db.update_receipt_status(
                receipt_id, "failed", {"error": f"Could not load image: {image_path}"}
            )
            return False

        logger.info(f"Image loaded: {image.shape}")

        # Step 1: OCR Processing
        logger.info(f"Step 1: Extracting text from receipt {receipt_id}...")
        receipt_data = process_receipt(image)

        if not receipt_data.get("merchant") and not receipt_data.get("total"):
            logger.warning(
                f"No merchant or total found for receipt {receipt_id} - OCR may have failed"
            )

        logger.info(
            f"OCR complete for {receipt_id} - Merchant: {receipt_data.get('merchant', 'Unknown')}"
        )

        # Step 2: Expense Classification
        logger.info(f"Step 2: Classifying expense category for receipt {receipt_id}...")
        receipt_data = add_category_to_receipt(receipt_data)

        logger.info(
            f"Classification complete for {receipt_id} - Category: {receipt_data['category']}"
        )

        # Step 3: Update receipt in database
        logger.info(f"Step 3: Updating receipt {receipt_id} in database...")
        update_data = {
            "merchant": receipt_data.get("merchant"),
            "date": receipt_data.get("date"),
            "total": receipt_data.get("total"),
            "tax": receipt_data.get("tax"),
            "subtotal": receipt_data.get("subtotal"),
            "items": receipt_data.get("items", []),
            "raw_text": receipt_data.get("raw_text"),
            "confidence": receipt_data.get("confidence"),
            "category": receipt_data.get("category"),
        }

        success = db.update_receipt_status(receipt_id, "completed", update_data)

        if success:
            logger.info(f"Receipt {receipt_id} processed successfully")
            return True
        else:
            logger.error(f"Failed to update receipt {receipt_id} in database")
            return False

    except Exception as e:
        logger.error(f"Error processing receipt {receipt_id}: {e}", exc_info=True)
        # Update status to failed
        try:
            db.update_receipt_status(receipt_id, "failed", {"error": str(e)})
        except Exception as update_error:
            logger.error(
                f"Failed to update receipt {receipt_id} status to failed: {update_error}"
            )
        return False


def main():
    """Main worker loop."""
    logger.info("Starting receipt processing worker...")

    # Initialize database
    try:
        db = ReceiptDatabase()
        if not db.connect():
            logger.error("Failed to connect to database")
            return

        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return

    # Main polling loop
    logger.info(f"Worker started. Polling every {POLL_INTERVAL} seconds...")
    try:
        while True:
            try:
                # Get pending receipts
                pending_receipts = db.get_pending_receipts(limit=10)

                if pending_receipts:
                    logger.info(f"Found {len(pending_receipts)} pending receipt(s)")

                    for receipt in pending_receipts:
                        process_pending_receipt(receipt, db)
                else:
                    logger.debug("No pending receipts found")

            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)

            # Wait before next poll
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    finally:
        db.disconnect()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
