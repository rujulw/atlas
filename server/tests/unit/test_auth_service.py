from app.services.auth import PBKDF2PasswordService


def test_hash_password_creates_expected_format() -> None:
    password_service = PBKDF2PasswordService()

    password_hash = password_service.hash_password("password123")
    scheme, algorithm, iterations, salt, digest = password_hash.split(":")

    assert scheme == "pbkdf2"
    assert algorithm == "sha256"
    assert iterations.isdigit()
    assert len(salt) == 32
    assert len(digest) == 64


def test_verify_password_returns_true_for_valid_password() -> None:
    password_service = PBKDF2PasswordService()
    password_hash = password_service.hash_password("password123")

    assert password_service.verify_password("password123", password_hash)


def test_verify_password_returns_false_for_invalid_password() -> None:
    password_service = PBKDF2PasswordService()
    password_hash = password_service.hash_password("password123")

    assert not password_service.verify_password("wrong-password", password_hash)


def test_verify_password_returns_false_for_invalid_hash_format() -> None:
    password_service = PBKDF2PasswordService()

    assert not password_service.verify_password("password123", "invalid-hash")
