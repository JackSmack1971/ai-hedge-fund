from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.backend.database.models import ApiKey
from app.backend.encryption import encrypt_value, is_encrypted


class ApiKeyRepository:
    """Repository for API key database operations.

    Secret values are encrypted before they touch the database (see
    app.backend.encryption); reads return ciphertext — use ApiKeyService
    to obtain decrypted values.
    """

    def __init__(self, db: Session):
        self.db = db

    def _reencrypt_if_plaintext(self, api_key: ApiKey) -> ApiKey:
        """Rewrite a legacy plaintext row as encrypted storage before returning it."""
        if not is_encrypted(api_key.key_value):
            api_key.key_value = encrypt_value(api_key.key_value)
            api_key.updated_at = func.now()
            self.db.commit()
            self.db.refresh(api_key)
        return api_key

    def create_or_update_api_key(
        self, provider: str, key_value: str, description: Optional[str] = None, is_active: bool = True
    ) -> ApiKey:
        """Create a new API key or update existing one"""
        # Check if API key already exists for this provider
        existing_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()

        if existing_key:
            # Update existing key
            existing_key.key_value = encrypt_value(key_value)
            existing_key.description = description
            existing_key.is_active = is_active
            existing_key.updated_at = func.now()
            self.db.commit()
            self.db.refresh(existing_key)
            return existing_key
        else:
            # Create new key
            api_key = ApiKey(
                provider=provider, key_value=encrypt_value(key_value), description=description, is_active=is_active
            )
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
            return api_key

    def get_api_key_by_provider(self, provider: str) -> Optional[ApiKey]:
        """Get API key by provider name"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider, ApiKey.is_active == True).first()
        return self._reencrypt_if_plaintext(api_key) if api_key else None

    def get_all_api_keys(self, include_inactive: bool = False) -> List[ApiKey]:
        """Get all API keys"""
        query = self.db.query(ApiKey)
        if not include_inactive:
            query = query.filter(ApiKey.is_active == True)
        api_keys = query.order_by(ApiKey.provider).all()
        plaintext_found = False
        for api_key in api_keys:
            if not is_encrypted(api_key.key_value):
                plaintext_found = True
                api_key.key_value = encrypt_value(api_key.key_value)
                api_key.updated_at = func.now()
        if plaintext_found:
            self.db.commit()
            for api_key in api_keys:
                self.db.refresh(api_key)
        return api_keys

    def update_api_key(
        self, provider: str, key_value: Optional[str] = None, description: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Optional[ApiKey]:
        """Update an existing API key"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return None

        if key_value is not None:
            api_key.key_value = encrypt_value(key_value)
        if description is not None:
            api_key.description = description
        if is_active is not None:
            api_key.is_active = is_active

        api_key.updated_at = func.now()
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def delete_api_key(self, provider: str) -> bool:
        """Delete an API key by provider"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return False

        self.db.delete(api_key)
        self.db.commit()
        return True

    def deactivate_api_key(self, provider: str) -> bool:
        """Deactivate an API key instead of deleting it"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider).first()
        if not api_key:
            return False

        api_key.is_active = False
        api_key.updated_at = func.now()
        self.db.commit()
        return True

    def update_last_used(self, provider: str) -> bool:
        """Update the last_used timestamp for an API key"""
        api_key = self.db.query(ApiKey).filter(ApiKey.provider == provider, ApiKey.is_active == True).first()
        if not api_key:
            return False

        api_key.last_used = func.now()
        self.db.commit()
        return True

    def reencrypt_plaintext_keys(self) -> int:
        """Migrate legacy plaintext rows to encrypted storage. Returns rows migrated."""
        migrated = 0
        for api_key in self.db.query(ApiKey).all():
            if not is_encrypted(api_key.key_value):
                api_key.key_value = encrypt_value(api_key.key_value)
                api_key.updated_at = func.now()
                migrated += 1
        if migrated:
            self.db.commit()
        return migrated

    def count_plaintext_keys(self, include_inactive: bool = True) -> int:
        """Count rows that still store plaintext API keys."""
        query = self.db.query(ApiKey)
        if not include_inactive:
            query = query.filter(ApiKey.is_active == True)
        return sum(1 for api_key in query.all() if not is_encrypted(api_key.key_value))

    def bulk_create_or_update(self, api_keys_data: List[dict]) -> List[ApiKey]:
        """Bulk create or update multiple API keys"""
        results = []
        for data in api_keys_data:
            api_key = self.create_or_update_api_key(
                provider=data["provider"],
                key_value=data["key_value"],
                description=data.get("description"),
                is_active=data.get("is_active", True),
            )
            results.append(api_key)
        return results
