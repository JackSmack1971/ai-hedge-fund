from fastapi import HTTPException

from app.backend.main import app


def test_global_exception_handler_masks_internal_500_details(test_app):
    @app.get("/__internal_error_test__")
    def _boom():
        raise HTTPException(status_code=500, detail="sqlite:///super-secret.db")

    response = test_app.get("/__internal_error_test__")

    assert response.status_code == 500
    assert response.json() == {"detail": "An internal error occurred"}
    assert "super-secret.db" not in response.text
