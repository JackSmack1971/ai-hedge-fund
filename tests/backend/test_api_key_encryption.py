"""Tests for encryption-at-rest of stored API keys (DATABASE_ENCRYPTION_KEY)."""

import pytest
from cryptography.fernet import Fernet

from app.backend.database.models import ApiKey
from app.backend.encryption import (
    CIPHERTEXT_PREFIX,
    decrypt_value,
    DecryptionError,
    encrypt_value,
    EncryptionKeyMissingError,
    is_encrypted,
)
from app.backend.repositories.api_key_repository import ApiKeyRepository
from app.backend.services.api_key_service import ApiKeyService

SECRET = "sk-test-secret-abc123"


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch):
    monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", "unit-test-passphrase")


class TestEncryptionModule:
    def test_round_trip(self):
        ciphertext = encrypt_value(SECRET)
        assert ciphertext != SECRET
        assert ciphertext.startswith(CIPHERTEXT_PREFIX)
        assert decrypt_value(ciphertext) == SECRET

    def test_accepts_generated_fernet_key(self, monkeypatch):
        monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", Fernet.generate_key().decode())
        assert decrypt_value(encrypt_value(SECRET)) == SECRET

    def test_legacy_plaintext_passthrough(self):
        assert decrypt_value("plain-old-value") == "plain-old-value"

    def test_missing_key_fails_closed(self, monkeypatch):
        monkeypatch.delenv("DATABASE_ENCRYPTION_KEY", raising=False)
        with pytest.raises(EncryptionKeyMissingError):
            encrypt_value(SECRET)
        with pytest.raises(EncryptionKeyMissingError):
            decrypt_value(CIPHERTEXT_PREFIX + "abc")

    def test_missing_key_still_reads_legacy_plaintext(self, monkeypatch):
        monkeypatch.delenv("DATABASE_ENCRYPTION_KEY", raising=False)
        assert decrypt_value("legacy-plaintext") == "legacy-plaintext"

    def test_rotated_key_raises_descriptive_error(self, monkeypatch):
        ciphertext = encrypt_value(SECRET)
        monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", "a-different-passphrase")
        with pytest.raises(DecryptionError, match="DATABASE_ENCRYPTION_KEY"):
            decrypt_value(ciphertext)


class TestRepositoryEncryption:
    def test_create_stores_ciphertext(self, db_session):
        repo = ApiKeyRepository(db_session)
        repo.create_or_update_api_key(provider="OPENAI_API_KEY", key_value=SECRET)

        row = db_session.query(ApiKey).filter(ApiKey.provider == "OPENAI_API_KEY").one()
        assert row.key_value != SECRET
        assert is_encrypted(row.key_value)
        assert SECRET not in row.key_value

    def test_update_stores_ciphertext(self, db_session):
        repo = ApiKeyRepository(db_session)
        repo.create_or_update_api_key(provider="OPENAI_API_KEY", key_value="initial")
        repo.update_api_key(provider="OPENAI_API_KEY", key_value=SECRET)

        row = db_session.query(ApiKey).filter(ApiKey.provider == "OPENAI_API_KEY").one()
        assert is_encrypted(row.key_value)
        assert decrypt_value(row.key_value) == SECRET

    def test_missing_key_blocks_writes(self, db_session, monkeypatch):
        monkeypatch.delenv("DATABASE_ENCRYPTION_KEY", raising=False)
        repo = ApiKeyRepository(db_session)
        with pytest.raises(EncryptionKeyMissingError):
            repo.create_or_update_api_key(provider="OPENAI_API_KEY", key_value=SECRET)

    def test_reencrypt_plaintext_keys_migrates_legacy_rows(self, db_session):
        db_session.add(ApiKey(provider="LEGACY_KEY", key_value="legacy-plaintext", is_active=True))
        db_session.commit()

        repo = ApiKeyRepository(db_session)
        migrated = repo.reencrypt_plaintext_keys()

        assert migrated == 1
        row = db_session.query(ApiKey).filter(ApiKey.provider == "LEGACY_KEY").one()
        assert is_encrypted(row.key_value)
        assert decrypt_value(row.key_value) == "legacy-plaintext"
        # Second run is a no-op
        assert repo.reencrypt_plaintext_keys() == 0


class TestServiceDecryption:
    def test_round_trip_through_service(self, db_session):
        repo = ApiKeyRepository(db_session)
        repo.create_or_update_api_key(provider="OPENAI_API_KEY", key_value=SECRET)

        service = ApiKeyService(db_session)
        assert service.get_api_key("OPENAI_API_KEY") == SECRET
        assert service.get_api_keys_dict() == {"OPENAI_API_KEY": SECRET}

    def test_service_reads_legacy_plaintext(self, db_session):
        db_session.add(ApiKey(provider="LEGACY_KEY", key_value="legacy-plaintext", is_active=True))
        db_session.commit()

        service = ApiKeyService(db_session)
        assert service.get_api_key("LEGACY_KEY") == "legacy-plaintext"
