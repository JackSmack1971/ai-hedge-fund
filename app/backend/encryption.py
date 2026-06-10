"""Encryption-at-rest for stored API keys.

Secrets in the ``api_keys`` table are encrypted with Fernet (AES-128-CBC +
HMAC) using a key derived from the ``DATABASE_ENCRYPTION_KEY`` environment
variable. Ciphertext is stored with a ``fernet:`` prefix so legacy plaintext
rows written before encryption existed remain readable; they are re-encrypted
the next time they are written.

``DATABASE_ENCRYPTION_KEY`` accepts either a valid Fernet key (urlsafe base64,
32 bytes — generate one with ``python -c "from cryptography.fernet import
Fernet; print(Fernet.generate_key().decode())"``) or an arbitrary passphrase,
which is stretched to a Fernet key via SHA-256.

If the variable is unset, storing or decrypting keys fails closed with
:class:`EncryptionKeyMissingError`.
"""

import base64
import binascii
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

CIPHERTEXT_PREFIX = "fernet:"


class EncryptionKeyMissingError(RuntimeError):
    """Raised when DATABASE_ENCRYPTION_KEY is required but not configured."""


class DecryptionError(RuntimeError):
    """Raised when a stored secret cannot be decrypted with the configured key."""


def _build_fernet() -> Fernet:
    raw = os.environ.get("DATABASE_ENCRYPTION_KEY")
    if not raw:
        raise EncryptionKeyMissingError(
            "DATABASE_ENCRYPTION_KEY is not set; refusing to store or read API keys without encryption. "
            "Set it in your environment (any passphrase works; a generated Fernet key is recommended)."
        )
    try:
        return Fernet(raw.encode())
    except (ValueError, binascii.Error):
        # Not a valid Fernet key — treat it as a passphrase and derive one
        derived = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
        return Fernet(derived)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a secret for storage; result carries the ciphertext prefix."""
    return CIPHERTEXT_PREFIX + _build_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(stored: str) -> str:
    """Decrypt a stored secret; legacy plaintext rows are returned unchanged."""
    if not stored.startswith(CIPHERTEXT_PREFIX):
        return stored
    token = stored.removeprefix(CIPHERTEXT_PREFIX)
    try:
        return _build_fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError(
            "Failed to decrypt a stored API key: DATABASE_ENCRYPTION_KEY does not match the key "
            "that encrypted it. Restore the original key, or delete and re-save the stored API keys."
        ) from exc


def is_encrypted(stored: str) -> bool:
    return stored.startswith(CIPHERTEXT_PREFIX)
