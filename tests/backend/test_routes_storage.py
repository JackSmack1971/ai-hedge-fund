"""Regression tests for /storage/save-json response behavior and path-traversal protection."""

import pytest
from fastapi.testclient import TestClient


def test_save_json_returns_success_and_filename(test_app: TestClient):
    response = test_app.post("/storage/save-json", json={"filename": "test-save.json", "data": {"k": "v"}})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["filename"] == "test-save.json"


@pytest.mark.parametrize(
    "filename",
    [
        "../evil.json",
        "../../etc/passwd",
        "..",
        "subdir/evil.json",
        "/tmp/evil.json",
        "\\windows\\evil.json",
        "..\\evil.json",
        ".hidden.json",
        "a/../../evil.json",
        "",
    ],
)
def test_save_json_rejects_unsafe_filenames(test_app: TestClient, filename: str):
    response = test_app.post("/storage/save-json", json={"filename": filename, "data": {"k": "v"}})

    assert response.status_code == 400, f"{filename!r} should be rejected, got {response.status_code}: {response.text}"
    assert "Invalid filename" in response.json()["detail"]


def test_save_json_traversal_does_not_write_outside_outputs(test_app: TestClient, tmp_path):
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    escaped_target = project_root / "evil-traversal-test.json"
    escaped_target.unlink(missing_ok=True)

    response = test_app.post(
        "/storage/save-json",
        json={"filename": "../evil-traversal-test.json", "data": {"pwned": True}},
    )

    assert response.status_code == 400
    assert not escaped_target.exists(), "traversal payload escaped the outputs directory"
