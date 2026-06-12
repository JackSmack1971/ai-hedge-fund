"""Encryption-at-rest for stored API keys.

Secrets in the ``api_keys`` table are encrypted with Fernet (AES-128-CBC +
HMAC) using a key derived from the ``DATABASE_ENCRYPTION_KEY`` environment
variable. Ciphertext uses a versioned prefix so the current derivation can
change without breaking existing rows. Legacy plaintext rows written before
encryption existed remain readable; they are re-encrypted the next time they
are written.

``DATABASE_ENCRYPTION_KEY`` accepts either a valid Fernet key (urlsafe base64,
32 bytes — generate one with ``python -c "from cryptography.fernet import
Fernet; print(Fernet.generate_key().decode())"``) or an arbitrary passphrase.
Passphrases are stretched with PBKDF2-HMAC-SHA256 and a fixed application salt
before use. Existing legacy ``fernet:`` ciphertexts remain decryptable during
migration.

If the variable is unset, storing or decrypting keys fails closed with
:class:`EncryptionKeyMissingError`.
"""

import base64
import binascii
import hashlib
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.backend.config import backend_settings

LEGACY_CIPHERTEXT_PREFIX = "fernet:"
CIPHERTEXT_PREFIX = "fernet2:"
PBKDF2_SALT = b"ai-hedge-fund-database-encryption"
PBKDF2_ITERATIONS = 600_000


class EncryptionKeyMissingError(RuntimeError):
    """Raised when DATABASE_ENCRYPTION_KEY is required but not configured."""


class DecryptionError(RuntimeError):
    """Raised when a stored secret cannot be decrypted with the configured key."""


def _get_raw_key() -> str:
    raw = backend_settings.database_encryption_key
    if not raw:
        raise EncryptionKeyMissingError(
            "DATABASE_ENCRYPTION_KEY is not set; refusing to store or read API keys without encryption. "
            "Set it in your environment (any passphrase works; a generated Fernet key is recommended)."
        )
    return raw


def _fernet_from_raw_key(raw: str) -> Optional[Fernet]:
    try:
        return Fernet(raw.encode())
    except (ValueError, binascii.Error):
        return None


@lru_cache(maxsize=None)
def _build_fernet(version: str, raw: str) -> Fernet:
    direct_key = _fernet_from_raw_key(raw)
    if direct_key is not None:
        return direct_key

    if version == "legacy":
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    elif version == "v2":
        derived = base64.urlsafe_b64encode(
            hashlib.pbkdf2_hmac("sha256", raw.encode(), PBKDF2_SALT, PBKDF2_ITERATIONS)
        )
    else:
        raise ValueError(f"Unsupported encryption version: {version}")

    return Fernet(derived)


def _build_legacy_fernet() -> Fernet:
    return _build_fernet("legacy", _get_raw_key())


def _build_current_fernet() -> Fernet:
    return _build_fernet("v2", _get_raw_key())


def encrypt_value(plaintext: str) -> str:
    """Encrypt a secret for storage; result carries the ciphertext prefix."""
    return CIPHERTEXT_PREFIX + _build_current_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(stored: str) -> str:
    """Decrypt a stored secret; legacy plaintext rows are returned unchanged."""
    if stored.startswith(CIPHERTEXT_PREFIX):
        token = stored.removeprefix(CIPHERTEXT_PREFIX)
        decryptor = _build_current_fernet()
    elif stored.startswith(LEGACY_CIPHERTEXT_PREFIX):
        token = stored.removeprefix(LEGACY_CIPHERTEXT_PREFIX)
        decryptor = _build_legacy_fernet()
    else:
        return stored
    try:
        return decryptor.decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError(
            "Failed to decrypt a stored API key: DATABASE_ENCRYPTION_KEY does not match the key "
            "that encrypted it. Restore the original key, or delete and re-save the stored API keys."
        ) from exc


def is_encrypted(stored: str) -> bool:
    return stored.startswith((CIPHERTEXT_PREFIX, LEGACY_CIPHERTEXT_PREFIX))
