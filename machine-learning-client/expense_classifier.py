"""
Expense Classifier Module.

This module classifies receipts into expense categories using zero-shot
classification with BART model from Hugging Face Transformers.
"""

import logging
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable for lazy initialization
_classifier = None

# Expense categories
EXPENSE_CATEGORIES = [
    "Dining",
    "Groceries",
    "Transportation",
    "Office Supplies",
    "Travel & Lodging",
    "Entertainment",
    "Utilities",
    "Healthcare",
    "Shopping",
    "Sports & Fitness",
    "Other",
]


def _get_classifier():
    """
    Get or initialize the zero-shot classification pipeline (lazy initialization).

    Returns:
        pipeline: Initialized Hugging Face zero-shot classification pipeline.
    """
    global _classifier
    if _classifier is None:
        logger.info("Initializing BART zero-shot classifier...")
        try:
            from transformers import pipeline

            _classifier = pipeline(
                "zero-shot-classification", model="facebook/bart-large-mnli"
            )
            logger.info("Classifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize classifier: {e}")
            raise
    return _classifier


def classify_expense(receipt_data: Dict[str, Any]) -> str:
    """
    Classify a receipt into an expense category.

    Uses the merchant name, item descriptions, and GPT's category hint to determine
    the most appropriate expense category using zero-shot classification.

    Args:
        receipt_data: Dictionary containing receipt information with keys:
            - merchant (str): Store/merchant name
            - items (List[Dict]): List of purchased items
            - category_hint (str, optional): GPT's suggested category for context
            - total (float): Total amount (optional, not used for classification)

    Returns:
        str: The expense category (one of EXPENSE_CATEGORIES)

    Example:
        >>> receipt = {"merchant": "Starbucks", "items": [{"name": "Coffee"}]}
        >>> category = classify_expense(receipt)
        >>> print(category)  # "Dining"
    """
    # Extract merchant name
    merchant = receipt_data.get("merchant", "")

    # Extract item names
    items = receipt_data.get("items", [])
    item_names = [item.get("name", "") for item in items if item.get("name")]

    # Get GPT's category hint if available
    category_hint = receipt_data.get("category_hint", "")

    # Build text to classify with GPT hint as context
    text_parts = []
    if merchant:
        text_parts.append(merchant)
    if item_names:
        text_parts.append(", ".join(item_names))
    if category_hint:
        # Add GPT's hint as contextual information
        text_parts.append(f"(likely {category_hint})")

    # Combine into single text
    if text_parts:
        text_to_classify = " ".join(text_parts)
    else:
        # No merchant or items - default to "Other"
        logger.warning("No merchant or items found in receipt, defaulting to 'Other'")
        return "Other"

    try:
        # Get classifier
        classifier = _get_classifier()

        # Run zero-shot classification
        result = classifier(text_to_classify, candidate_labels=EXPENSE_CATEGORIES)

        # Return the top predicted category
        category = result["labels"][0]
        confidence = result["scores"][0]

        logger.info(
            f"Classified '{merchant}' as '{category}' (confidence: {confidence:.2f})"
        )

        return category

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        # Default to "Other" on error
        return "Other"


def add_category_to_receipt(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add expense category to receipt data.

    This is a convenience function that adds the 'category' field
    to the receipt data dictionary.

    Args:
        receipt_data: Receipt data dictionary from OCR processor

    Returns:
        Dict: Receipt data with added 'category' field

    Example:
        >>> receipt = {"merchant": "Target", "total": 45.67}
        >>> receipt_with_category = add_category_to_receipt(receipt)
        >>> print(receipt_with_category["category"])  # "Shopping"
    """
    category = classify_expense(receipt_data)
    receipt_data["category"] = category
    return receipt_data
