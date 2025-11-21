"""
Tests for the expense categories endpoint.
"""


def test_categories(client, logged_in_user):  # pylint: disable=unused-argument
    """Test that /api/receipts/categories returns a non-empty list."""
    res = client.get("/api/receipts/categories")
    assert res.status_code == 200
    assert "categories" in res.json
    assert isinstance(res.json["categories"], list)
    assert len(res.json["categories"]) > 0
