"""
Tests for receipt CRUD operations: list, get, update, delete.
"""

import io


def _upload(client):
    """Helper function to upload a test receipt image."""
    data = {"file": (io.BytesIO(b"abc"), "test.jpg")}
    res = client.post(
        "/api/receipts/upload", data=data, content_type="multipart/form-data"
    )
    return res.json["receipt_id"]


def test_receipt_crud_flow(client, logged_in_user):  # pylint: disable=unused-argument
    """Test full receipt lifecycle: upload, list, get, update, delete."""
    receipt_id = _upload(client)

    # list
    r_list = client.get("/api/receipts/")
    assert r_list.status_code == 200
    assert len(r_list.json["receipts"]) >= 1

    # get
    r_get = client.get(f"/api/receipts/{receipt_id}")
    assert r_get.status_code == 200

    # update
    r_patch = client.patch(
        f"/api/receipts/{receipt_id}", json={"merchant": "Starbucks"}
    )
    assert r_patch.status_code == 200

    # delete
    r_del = client.delete(f"/api/receipts/{receipt_id}")
    assert r_del.status_code == 200
