import io

def test_upload_no_file(client, logged_in_user):
    res = client.post("/api/receipts/upload")
    assert res.status_code == 400


def test_upload_valid_file(client, logged_in_user):
    data = {
        "file": (io.BytesIO(b"fakebytes"), "receipt.jpg")
    }

    res = client.post(
        "/api/receipts/upload",
        data=data,
        content_type="multipart/form-data",
    )

    assert res.status_code == 201
    assert "receipt_id" in res.json
    assert res.json["status"] == "pending"