"""
Unit tests for expense_classifier module.

Tests all classification functions with mocked BART model to avoid
downloading large model files during testing.
"""

import pytest
import datetime
from unittest.mock import MagicMock, patch
from expense_classifier import (
    EXPENSE_CATEGORIES,
    classify_expense,
    add_category_to_receipt,
)

# Unique test data using timestamp
random_time = datetime.datetime.now().time()
test_merchant = f"Test Merchant {random_time}"


class TestExpenseCategories:
    """Test suite for expense categories and classification."""

    def test_sanity_check(self):
        """
        Test debugging - making sure that we can run a simple test that always passes.
        """
        expected = True
        actual = True
        assert actual == expected, "Expected True to be equal to True!"

    def test_expense_categories_exist(self):
        """Verify that EXPENSE_CATEGORIES list is defined and not empty."""
        assert EXPENSE_CATEGORIES is not None, "EXPENSE_CATEGORIES should not be None"
        assert len(EXPENSE_CATEGORIES) > 0, "EXPENSE_CATEGORIES should not be empty"
        assert all(
            isinstance(cat, str) for cat in EXPENSE_CATEGORIES
        ), "All categories should be strings"

    def test_expense_categories_count(self):
        """Verify we have exactly 10 expense categories."""
        assert len(EXPENSE_CATEGORIES) == 10, "Should have exactly 10 categories"

    def test_expense_categories_content(self):
        """Verify specific expected categories are present."""
        expected_categories = [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Healthcare",
            "Other",
        ]
        for category in expected_categories:
            assert (
                category in EXPENSE_CATEGORIES
            ), f"{category} should be in EXPENSE_CATEGORIES"

    def test_no_duplicate_categories(self):
        """Verify there are no duplicate categories."""
        unique_categories = set(EXPENSE_CATEGORIES)
        assert len(unique_categories) == len(
            EXPENSE_CATEGORIES
        ), "EXPENSE_CATEGORIES should not contain duplicates"


class TestClassifyExpense:
    """Test suite for classify_expense function."""

    @pytest.fixture
    def mock_classifier(self):
        """
        Create a mocked transformer pipeline for testing.
        This fixture sets up a mocked classifier before each test.
        """
        with patch("expense_classifier._get_classifier") as mock_get_classifier:
            # Create mock classifier
            mock_pipeline = MagicMock()
            mock_get_classifier.return_value = mock_pipeline

            yield mock_pipeline

    def test_classify_food_merchant(self, mock_classifier):
        """Test classification of food & dining merchant."""
        # Mock classifier response
        mock_classifier.return_value = {
            "labels": ["Food & Dining", "Shopping", "Other"],
            "scores": [0.95, 0.03, 0.02],
        }

        receipt = {"merchant": "Starbucks", "items": [{"name": "Coffee"}], "total": 5.99}

        category = classify_expense(receipt)

        assert category == "Food & Dining", "Starbucks should be Food & Dining"
        mock_classifier.assert_called_once()

    def test_classify_transportation_merchant(self, mock_classifier):
        """Test classification of transportation merchant."""
        mock_classifier.return_value = {
            "labels": ["Transportation", "Other", "Shopping"],
            "scores": [0.92, 0.05, 0.03],
        }

        receipt = {"merchant": "Uber", "items": [], "total": 25.00}

        category = classify_expense(receipt)

        assert category == "Transportation", "Uber should be Transportation"

    def test_classify_shopping_merchant(self, mock_classifier):
        """Test classification of shopping merchant."""
        mock_classifier.return_value = {
            "labels": ["Shopping", "Other", "Food & Dining"],
            "scores": [0.88, 0.08, 0.04],
        }

        receipt = {
            "merchant": "Target",
            "items": [{"name": "Shampoo"}, {"name": "Toothpaste"}],
            "total": 15.50,
        }

        category = classify_expense(receipt)

        assert category == "Shopping", "Target should be Shopping"

    def test_classify_healthcare_merchant(self, mock_classifier):
        """Test classification of healthcare merchant."""
        mock_classifier.return_value = {
            "labels": ["Healthcare", "Shopping", "Other"],
            "scores": [0.90, 0.06, 0.04],
        }

        receipt = {
            "merchant": "CVS Pharmacy",
            "items": [{"name": "Prescription"}],
            "total": 45.00,
        }

        category = classify_expense(receipt)

        assert category == "Healthcare", "CVS Pharmacy should be Healthcare"

    def test_classify_utilities_merchant(self, mock_classifier):
        """Test classification of utilities merchant."""
        mock_classifier.return_value = {
            "labels": ["Utilities", "Other", "Shopping"],
            "scores": [0.85, 0.10, 0.05],
        }

        receipt = {"merchant": "Con Edison", "items": [], "total": 150.00}

        category = classify_expense(receipt)

        assert category == "Utilities", "Con Edison should be Utilities"

    def test_classify_entertainment_merchant(self, mock_classifier):
        """Test classification of entertainment merchant."""
        mock_classifier.return_value = {
            "labels": ["Entertainment", "Shopping", "Other"],
            "scores": [0.93, 0.04, 0.03],
        }

        receipt = {"merchant": "AMC Theaters", "items": [{"name": "Movie Ticket"}]}

        category = classify_expense(receipt)

        assert category == "Entertainment", "AMC Theaters should be Entertainment"

    def test_classify_with_items_only(self, mock_classifier):
        """Test classification using item names when merchant is unclear."""
        mock_classifier.return_value = {
            "labels": ["Food & Dining", "Shopping", "Other"],
            "scores": [0.87, 0.08, 0.05],
        }

        receipt = {
            "merchant": "Corner Store",
            "items": [{"name": "Pizza"}, {"name": "Soda"}],
            "total": 12.00,
        }

        category = classify_expense(receipt)

        assert category == "Food & Dining", "Pizza items should be Food & Dining"

    def test_classify_empty_merchant_with_items(self, mock_classifier):
        """Test classification with empty merchant but valid items."""
        mock_classifier.return_value = {
            "labels": ["Shopping", "Other", "Food & Dining"],
            "scores": [0.80, 0.12, 0.08],
        }

        receipt = {"merchant": "", "items": [{"name": "Shoes"}], "total": 60.00}

        category = classify_expense(receipt)

        assert category == "Shopping", "Should classify based on items only"

    def test_classify_no_merchant_no_items(self):
        """Test classification with no merchant and no items - should default to Other."""
        receipt = {"merchant": "", "items": [], "total": 10.00}

        category = classify_expense(receipt)

        assert (
            category == "Other"
        ), "Empty receipt should default to Other without calling classifier"

    def test_classify_missing_merchant_field(self):
        """Test classification when merchant field is missing."""
        receipt = {"items": [{"name": "Unknown Item"}], "total": 20.00}

        category = classify_expense(receipt)

        # Should still work and return a valid category
        assert category in EXPENSE_CATEGORIES, "Should return valid category"

    def test_classify_missing_items_field(self, mock_classifier):
        """Test classification when items field is missing."""
        mock_classifier.return_value = {
            "labels": ["Shopping", "Other", "Food & Dining"],
            "scores": [0.75, 0.15, 0.10],
        }

        receipt = {"merchant": "Amazon", "total": 50.00}

        category = classify_expense(receipt)

        assert (
            category in EXPENSE_CATEGORIES
        ), "Should return valid category even without items"

    def test_classify_items_with_empty_names(self, mock_classifier):
        """Test classification with items that have empty names."""
        mock_classifier.return_value = {
            "labels": ["Food & Dining", "Other", "Shopping"],
            "scores": [0.82, 0.12, 0.06],
        }

        receipt = {
            "merchant": "McDonald's",
            "items": [{"name": ""}, {"name": "Burger"}, {"name": ""}],
            "total": 8.50,
        }

        category = classify_expense(receipt)

        assert category == "Food & Dining", "Should filter out empty item names"

    @patch("expense_classifier._get_classifier")
    def test_classification_error_handling(self, mock_get_classifier):
        """Test that classification errors are handled gracefully."""
        # Make classifier raise an exception
        mock_get_classifier.side_effect = Exception("Model failed to load")

        receipt = {"merchant": "Test Store", "items": [], "total": 10.00}

        category = classify_expense(receipt)

        assert category == "Other", "Should return 'Other' when classification fails"

    def test_classify_returns_valid_category(self, mock_classifier):
        """Test that classify_expense always returns a valid category."""
        mock_classifier.return_value = {
            "labels": ["Sports & Fitness", "Shopping", "Other"],
            "scores": [0.88, 0.08, 0.04],
        }

        receipt = {"merchant": "Nike", "items": [{"name": "Running Shoes"}]}

        category = classify_expense(receipt)

        assert (
            category in EXPENSE_CATEGORIES
        ), f"'{category}' should be in EXPENSE_CATEGORIES"


class TestAddCategoryToReceipt:
    """Test suite for add_category_to_receipt function."""

    @patch("expense_classifier.classify_expense")
    def test_add_category_to_receipt(self, mock_classify):
        """Test adding category to receipt data."""
        mock_classify.return_value = "Food & Dining"

        receipt = {"merchant": "Chipotle", "total": 12.50, "items": []}

        result = add_category_to_receipt(receipt)

        assert "category" in result, "Receipt should have 'category' field"
        assert result["category"] == "Food & Dining", "Category should be Food & Dining"
        mock_classify.assert_called_once_with(receipt)

    @patch("expense_classifier.classify_expense")
    def test_add_category_preserves_other_fields(self, mock_classify):
        """Test that adding category preserves all other receipt fields."""
        mock_classify.return_value = "Shopping"

        receipt = {
            "merchant": "Walmart",
            "total": 45.67,
            "tax": 3.50,
            "date": "2025-11-18",
            "items": [{"name": "Milk", "price": 4.99}],
        }

        result = add_category_to_receipt(receipt)

        # Check all original fields are preserved
        assert result["merchant"] == "Walmart", "Merchant should be preserved"
        assert result["total"] == 45.67, "Total should be preserved"
        assert result["tax"] == 3.50, "Tax should be preserved"
        assert result["date"] == "2025-11-18", "Date should be preserved"
        assert len(result["items"]) == 1, "Items should be preserved"
        assert result["category"] == "Shopping", "Category should be added"

    @patch("expense_classifier.classify_expense")
    def test_add_category_overwrites_existing(self, mock_classify):
        """Test that adding category overwrites existing category field."""
        mock_classify.return_value = "Food & Dining"

        receipt = {"merchant": "Starbucks", "category": "Other", "total": 5.99}

        result = add_category_to_receipt(receipt)

        assert (
            result["category"] == "Food & Dining"
        ), "Should overwrite existing category"

