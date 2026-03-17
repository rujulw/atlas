from app.core.config import settings
from app.services.identity import (
    EncryptedIdentityValue,
    HMACSHA256BlindIndexService,
    IdentityCryptoSettings,
    normalize_email,
)


def test_identity_crypto_settings_are_exposed_in_app_config() -> None:
    assert settings.IDENTITY_ENCRYPTION_KEY
    assert settings.IDENTITY_BLIND_INDEX_KEY
    assert settings.IDENTITY_KEY_VERSION == "v1"


def test_identity_crypto_settings_value_object_captures_expected_fields() -> None:
    crypto_settings = IdentityCryptoSettings(
        encryption_key="enc-key",
        blind_index_key="blind-key",
        key_version="v2",
    )
    encrypted_value = EncryptedIdentityValue(ciphertext="ciphertext", key_version="v2")

    assert crypto_settings.encryption_key == "enc-key"
    assert crypto_settings.blind_index_key == "blind-key"
    assert crypto_settings.key_version == "v2"
    assert encrypted_value.ciphertext == "ciphertext"
    assert encrypted_value.key_version == "v2"


def test_normalize_email_strips_whitespace_and_lowercases() -> None:
    assert normalize_email("  User@Example.COM ") == "user@example.com"


def test_blind_index_service_is_deterministic_for_normalized_value() -> None:
    blind_index_service = HMACSHA256BlindIndexService(key="blind-key")

    normalized_email = normalize_email("User@Example.COM")

    assert blind_index_service.derive(normalized_email) == blind_index_service.derive(
        "user@example.com"
    )
