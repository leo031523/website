import pytest
from app.core.crypto import DecryptionError, decrypt_secret, encrypt_secret, mask_secret


def test_encrypt_decrypt_round_trip():
    plain = "sk-super-secret-api-key-123456"
    encrypted = encrypt_secret(plain)
    assert encrypted != plain
    assert decrypt_secret(encrypted) == plain


def test_encrypted_value_is_not_plaintext_substring():
    plain = "my-api-key-abcdef"
    encrypted = encrypt_secret(plain)
    assert plain not in encrypted


def test_decrypt_garbage_raises_decryption_error():
    with pytest.raises(DecryptionError):
        decrypt_secret("not-a-real-fernet-token")


def test_mask_secret_only_shows_last_four_chars():
    masked = mask_secret("sk-abcdefgh1234")
    assert masked == "****1234"
    assert "abcdefgh" not in masked


def test_mask_secret_handles_short_strings():
    masked = mask_secret("ab")
    assert masked == "**"
