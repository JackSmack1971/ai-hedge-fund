"""Tests for API-key plaintext migration during startup."""

import logging
from unittest.mock import MagicMock, patch

from app.backend.main import _reencrypt_plaintext_api_keys_on_startup


@patch("app.backend.database.connection.SessionLocal")
@patch("app.backend.main.ApiKeyRepository")
def test_startup_logs_plaintext_migration_when_rows_are_reencrypted(mock_repo_cls, mock_session_local, caplog):
    db = MagicMock()
    mock_session_local.return_value = db
    repo = mock_repo_cls.return_value
    repo.reencrypt_plaintext_keys.return_value = 2

    with caplog.at_level(logging.WARNING):
        _reencrypt_plaintext_api_keys_on_startup()

    repo.reencrypt_plaintext_keys.assert_called_once()
    assert "Re-encrypted 2 legacy plaintext API key row(s) at startup" in caplog.text
    db.close.assert_called_once()
