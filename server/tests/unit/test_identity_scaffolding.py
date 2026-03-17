from app.core.config import settings
from app.services.identity import EncryptedIdentityValue, IdentityCryptoSettings


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
