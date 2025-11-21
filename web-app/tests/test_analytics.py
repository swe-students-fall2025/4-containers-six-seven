"""Test analytics"""
import database  # IMPORTANT: import the module, not db directly


def test_analytics(client, logged_in_user):
    """
    Verify aggregated analytics results.
    """

    # Insert mock receipts using the patched DB
    database.db.receipts.insert_many(
        [
            {
                "user_id": logged_in_user["_id"],
                "status": "completed",
                "total": 10.0,
                "category": "Dining",
                "date": "2025-01-15",
            },
            {
                "user_id": logged_in_user["_id"],
                "status": "completed",
                "total": 25.50,
                "category": "Groceries",
                "date": "2025-01-20",
            },
        ]
    )

    # Call analytics endpoint
    res = client.get("/api/receipts/analytics")
    assert res.status_code == 200

    data = res.json

    # Validate structure
    assert "category_totals" in data
    assert "monthly_totals" in data
    assert "count" in data

    # Validate values
    assert data["category_totals"]["Dining"] == 10.0
    assert data["category_totals"]["Groceries"] == 25.50
    assert data["monthly_totals"]["2025-01"] == 35.50
    assert data["count"] == 2
