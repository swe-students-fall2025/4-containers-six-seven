"""
Main orchestration script for Receipt Scanner ML Client.

This script integrates OCR processing, expense classification, and database storage
to provide a complete receipt scanning pipeline with CLI interface.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import cv2

# Import our modules
from ocr_processor import process_receipt
from expense_classifier import add_category_to_receipt
from database import ReceiptDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def process_single_receipt(image_path: str, db: ReceiptDatabase) -> Dict[str, Any]:
    """
    Process a single receipt image through the complete pipeline.

    Pipeline: Image → OCR → Classification → Database Storage

    Args:
        image_path: Path to the receipt image file
        db: Database instance for storing results

    Returns:
        Dict containing the processed receipt data with category

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image cannot be loaded
    """
    logger.info(f"Processing receipt: {image_path}")

    # Check if file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    logger.info(f"Image loaded: {image.shape}")

    # Step 1: OCR Processing (Person 2's module)
    logger.info("Step 1: Extracting text from receipt...")
    receipt_data = process_receipt(image)

    if not receipt_data.get("merchant") and not receipt_data.get("total"):
        logger.warning("No merchant or total found - OCR may have failed")

    logger.info(f"OCR complete - Merchant: {receipt_data.get('merchant', 'Unknown')}")

    # Step 2: Expense Classification (Person 3's module)
    logger.info("Step 2: Classifying expense category...")
    receipt_data = add_category_to_receipt(receipt_data)

    logger.info(f"Classification complete - Category: {receipt_data['category']}")

    # Step 3: Database Storage (Person 3's module)
    logger.info("Step 3: Storing receipt in database...")
    receipt_id = db.insert_receipt(receipt_data)

    if receipt_id:
        logger.info(f"Receipt stored successfully - ID: {receipt_id}")
        receipt_data["_id"] = receipt_id
    else:
        logger.error("Failed to store receipt in database")

    return receipt_data


def process_batch(directory: str, db: ReceiptDatabase) -> Dict[str, Any]:
    """
    Process all receipt images in a directory.

    Args:
        directory: Path to directory containing receipt images
        db: Database instance for storing results

    Returns:
        Dict containing summary statistics

    Raises:
        NotADirectoryError: If directory doesn't exist
    """
    logger.info(f"Batch processing directory: {directory}")

    # Check if directory exists
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory}")

    # Find all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    image_files = [
        f for f in dir_path.iterdir()
        if f.suffix.lower() in image_extensions
    ]

    if not image_files:
        logger.warning(f"No image files found in {directory}")
        return {"processed": 0, "failed": 0, "total": 0}

    logger.info(f"Found {len(image_files)} image files")

    # Process each image
    results = {"processed": 0, "failed": 0, "total": len(image_files)}
    failed_files = []

    for i, image_file in enumerate(image_files, 1):
        logger.info(f"[{i}/{len(image_files)}] Processing {image_file.name}")

        try:
            process_single_receipt(str(image_file), db)
            results["processed"] += 1
        except Exception as e:
            logger.error(f"Failed to process {image_file.name}: {e}")
            results["failed"] += 1
            failed_files.append(image_file.name)

    # Summary
    logger.info("=" * 60)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info(f"Total files: {results['total']}")
    logger.info(f"Successfully processed: {results['processed']}")
    logger.info(f"Failed: {results['failed']}")

    if failed_files:
        logger.info(f"Failed files: {', '.join(failed_files)}")

    logger.info("=" * 60)

    return results


def show_statistics(db: ReceiptDatabase):
    """
    Display database statistics.

    Args:
        db: Database instance
    """
    logger.info("Fetching database statistics...")

    stats = db.get_statistics()

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"\nTotal Receipts: {stats['total_receipts']}")
    print(f"Total Amount: ${stats['total_amount']:.2f}")

    if stats["by_category"]:
        print("\nBreakdown by Category:")
        print("-" * 60)

        for cat_stat in stats["by_category"]:
            category = cat_stat["_id"] or "Unknown"
            count = cat_stat["count"]
            total = cat_stat["total"]
            avg = total / count if count > 0 else 0

            print(f"  {category:20s}: {count:3d} receipts, ${total:8.2f} (avg: ${avg:.2f})")

    print("=" * 60 + "\n")


def main():
    """
    Main entry point for the receipt scanner ML client.

    Provides CLI interface for processing receipts, batch processing,
    and viewing statistics.
    """
    parser = argparse.ArgumentParser(
        description="Receipt Scanner ML Client - Process and classify receipt images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single receipt
  python main.py --image receipt.jpg

  # Process all receipts in a directory
  python main.py --batch ./receipts/

  # View database statistics
  python main.py --stats

  # Process receipt with custom database settings
  python main.py --image receipt.jpg --db-name my_receipts
        """
    )

    # Arguments
    parser.add_argument(
        "--image",
        type=str,
        help="Path to a single receipt image to process"
    )

    parser.add_argument(
        "--batch",
        type=str,
        help="Path to directory containing receipt images for batch processing"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display database statistics"
    )

    parser.add_argument(
        "--db-host",
        type=str,
        default="mongodb",
        help="MongoDB host (default: mongodb)"
    )

    parser.add_argument(
        "--db-name",
        type=str,
        help="MongoDB database name (overrides MONGO_DB_NAME env var)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check that at least one action is specified
    if not (args.image or args.batch or args.stats):
        parser.print_help()
        print("\nError: Must specify --image, --batch, or --stats")
        sys.exit(1)

    # Initialize database
    try:
        logger.info("Connecting to database...")
        db = ReceiptDatabase(
            mongo_db_name=args.db_name,
            mongo_host=args.db_host
        )

        if not db.connect():
            logger.error("Failed to connect to database")
            sys.exit(1)

        logger.info("Database connection established")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    # Execute requested action
    try:
        if args.image:
            # Process single image
            receipt_data = process_single_receipt(args.image, db)

            # Display results
            print("\n" + "=" * 60)
            print("RECEIPT PROCESSED SUCCESSFULLY")
            print("=" * 60)
            print(f"Merchant:  {receipt_data.get('merchant', 'Unknown')}")
            print(f"Date:      {receipt_data.get('date', 'Unknown')}")
            print(f"Total:     ${receipt_data.get('total', 0):.2f}")
            print(f"Category:  {receipt_data.get('category', 'Unknown')}")

            if receipt_data.get('items'):
                print(f"Items:     {len(receipt_data['items'])} item(s)")

            print(f"Confidence: {receipt_data.get('confidence', 0):.2%}")
            print("=" * 60 + "\n")

        elif args.batch:
            # Batch processing
            results = process_batch(args.batch, db)

            if results["processed"] == 0 and results["failed"] > 0:
                sys.exit(1)

        elif args.stats:
            # Show statistics
            show_statistics(db)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Clean up
        db.disconnect()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()

