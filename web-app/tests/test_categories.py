def test_categories(client, logged_in_user):
    res = client.get("/api/receipts/categories")
    assert res.status_code == 200
    assert "categories" in res.json
    assert isinstance(res.json["categories"], list)
    assert len(res.json["categories"]) > 0