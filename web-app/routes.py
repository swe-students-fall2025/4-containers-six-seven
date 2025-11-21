"""
Receipt-related REST API endpoints.

This module contains the CRUD endpoints for receipts,
analytics endpoints, category listing, and upload handlers.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from categories import EXPENSE_CATEGORIES
from database import db
from file_handler import allowed_file, save_uploaded_file

receipt_bp = Blueprint("receipts", __name__, url_prefix="/api/receipts")


# -------------------------------------------------------
# Upload Receipt
# -------------------------------------------------------
@receipt_bp.post("/upload")
@login_required
def upload_receipt():
    """
    Upload a new receipt image.

    Request (multipart/form-data):
        file: image file (png/jpg/jpeg)

    Response (201 Created):
    {
        "receipt_id": "65a123abcde...",
        "status": "pending"
    }

    Errors:
        400 - missing file, invalid file type
    """
    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400

    file = request.files["file"]

    if file.filename == "":
        return {"error": "Empty filename"}, 400

    if not allowed_file(file.filename):
        return {"error": "Invalid file type"}, 400

    # Save file to uploads directory
    path = save_uploaded_file(file)

    # Insert into DB as pending receipt (worker will process)
    receipt_id = db.insert_receipt(current_user.id, path)

    return {"receipt_id": receipt_id, "status": "pending"}, 201


# -------------------------------------------------------
# List Receipts
# -------------------------------------------------------
@receipt_bp.get("/")
@login_required
def list_receipts():
    """
    List all receipts belonging to the current user.

    Response (200 OK):
    {
        "receipts": [
            {
                "_id": "...",
                "status": "completed",
                "merchant": "Starbucks",
                "total": 8.45,
                ...
            }
        ]
    }
    """
    receipts = db.get_receipts_by_user(current_user.id)
    return {"receipts": receipts}, 200


# -------------------------------------------------------
# Get Single Receipt
# -------------------------------------------------------
@receipt_bp.get("/<receipt_id>")
@login_required
def get_receipt(receipt_id):
    """
    Fetch full receipt details.

    Response (200 OK):
    {
        "_id": "...",
        "merchant": "Target",
        "total": 19.99,
        "category": "Shopping",
        ...
    }

    Errors:
        404 - not found or belongs to another user
    """
    r = db.get_receipt_by_id(receipt_id)

    if not r or r["user_id"] != current_user.id:
        return {"error": "Receipt not found"}, 404

    return jsonify(r), 200


# -------------------------------------------------------
# Update Receipt (Manual Edit)
# -------------------------------------------------------
@receipt_bp.patch("/<receipt_id>")
@login_required
def update_receipt(receipt_id):
    """
    Update receipt fields manually.

    Request (JSON):
        {
            "merchant": "Starbucks",
            "total": 10.95
        }

    Response:
        200 OK → { "message": "Receipt updated" }
        400 Bad Request → update failed
    """
    data = request.json or {}

    success = db.update_receipt(receipt_id, data)
    if not success:
        return {"error": "Update failed"}, 400

    return {"message": "Receipt updated"}, 200


# -------------------------------------------------------
# Delete Receipt
# -------------------------------------------------------
@receipt_bp.delete("/<receipt_id>")
@login_required
def delete_receipt(receipt_id):
    """
    Delete a receipt.

    Response (200 OK):
        { "message": "Receipt deleted" }

    Errors:
        400 - delete failed
    """
    success = db.delete_receipt(receipt_id)
    if not success:
        return {"error": "Delete failed"}, 400

    return {"message": "Receipt deleted"}, 200


# -------------------------------------------------------
# Analytics
# -------------------------------------------------------
@receipt_bp.get("/analytics")
@login_required
def analytics():
    """
    Generate analytics for the user's receipts.

    These results feed the frontend charts.

    Response (200 OK):
    {
        "category_totals": {
            "Dining": 58.00,
            "Groceries": 130.00,
            ...
        },
        "monthly_totals": {
            "2025-01": 188.00,
            ...
        },
        "count": 12
    }

    Notes:
        - category missing → "Uncategorized"
        - date missing → excluded from monthly totals
        - date must be "YYYY-MM-DD"
    """
    receipts = db.get_receipts_by_user(current_user.id)

    category_totals = {}
    monthly_totals = {}

    for r in receipts:
        category = r.get("category") or "Uncategorized"
        total = r.get("total") or 0

        # Category totals
        category_totals[category] = category_totals.get(category, 0) + total

        # Monthly totals
        date = r.get("date")
        if date and len(date) >= 7:
            month = date[:7]  # 'YYYY-MM'
            monthly_totals[month] = monthly_totals.get(month, 0) + total

    return {
        "category_totals": category_totals,
        "monthly_totals": monthly_totals,
        "count": len(receipts),
    }, 200


# -------------------------------------------------------
# Get Categories
# -------------------------------------------------------
@receipt_bp.get("/categories")
@login_required
def get_categories():
    """
    Return the list of supported expense categories.

    Response (200 OK):
    {
        "categories": ["Dining", "Groceries", ...]
    }
    """
    return {"categories": EXPENSE_CATEGORIES}, 200


# -------------------------------------------------------
# Status Endpoint
# -------------------------------------------------------
@receipt_bp.get("/<receipt_id>/status")
@login_required
def receipt_status(receipt_id):
    """
    Fetch status of a specific receipt (used by polling UI).

    Response (200 OK):
    {
        "status": "completed",
        "category": "Dining",
        "merchant": "Starbucks",
        "total": 8.99
    }
    """
    r = db.get_receipt_by_id(receipt_id)

    if not r or r["user_id"] != current_user.id:
        return {"error": "Receipt not found"}, 404

    return {
        "status": r.get("status"),
        "category": r.get("category"),
        "merchant": r.get("merchant"),
        "total": r.get("total"),
    }, 200
