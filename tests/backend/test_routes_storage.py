"""Regression tests for /storage/save-json response behavior."""

from fastapi.testclient import TestClient


def test_save_json_returns_success_and_filename(test_app: TestClient):
    response = test_app.post("/storage/save-json", json={"filename": "test-save.json", "data": {"k": "v"}})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["filename"] == "test-save.json"

